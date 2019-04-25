from pyircbot.modulebase import ModuleBase, MissingDependancyException, command
from pyircbot.modules.ModInfo import info
from pyircbot.modules.NickUser import protected
from contextlib import closing
from decimal import Decimal
from time import sleep, time
from queue import Queue, Empty
from threading import Thread
from requests import get
from collections import namedtuple
from math import ceil
from datetime import datetime, timedelta
import re
import json
import traceback


RE_SYMBOL = re.compile(r'^([A-Z\-]+)$')
DUSTACCT = "#dust"

Trade = namedtuple("Trade", "nick buy symbol amount replyto")


def format_price(cents, prefix="$", plus=False):
    """
    Formats cents as a dollar value
    """
    return format_decimal((Decimal(cents) / 100) if cents > 0 else 0,  # avoids "-0.00" output
                          prefix, plus)


def format_decimal(decm, prefix="$", plus=False):
    """
    Formats a decimal as a dollar value
    """
    return "{}{}{:,.2f}".format(prefix, "+" if plus and decm >= 0 else "", decm)


class StockPlay(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.sqlite = self.bot.getBestModuleForService("sqlite")

        if self.sqlite is None:
            raise MissingDependancyException("StockPlay: SQLIite service is required.")

        self.sql = self.sqlite.opendb("stockplay.db")

        with closing(self.sql.getCursor()) as c:
            if not self.sql.tableExists("stockplay_balances"):
                c.execute("""CREATE TABLE `stockplay_balances` (
                      `nick` varchar(64) PRIMARY KEY,
                      `cents` integer
                    );""")
                c.execute("""INSERT INTO `stockplay_balances` VALUES (?, ?)""", (DUSTACCT, 0))
            if not self.sql.tableExists("stockplay_holdings"):
                c.execute("""CREATE TABLE `stockplay_holdings` (
                      `nick` varchar(64),
                      `symbol` varchar(12),
                      `count` integer,
                      PRIMARY KEY (nick, symbol)
                    );""")
            if not self.sql.tableExists("stockplay_trades"):
                c.execute("""CREATE TABLE `stockplay_trades` (
                      `nick` varchar(64),
                      `time` integer,
                      `type` varchar(8),
                      `symbol` varchar(12),
                      `count` integer,
                      `price` integer
                    );""")
            if not self.sql.tableExists("stockplay_prices"):
                c.execute("""CREATE TABLE `stockplay_prices` (
                      `symbol` varchar(12) PRIMARY KEY,
                      `time` integer,
                      `data` text
                    );""")
            if not self.sql.tableExists("stockplay_balance_history"):
                c.execute("""CREATE TABLE `stockplay_balance_history` (
                      `nick` varchar(64),
                      `day` text,
                      `cents` integer,
                      PRIMARY KEY(nick, day)
                    );""")

        # Last time the interval tasks were executed
        self.task_time = 0

        # background work executor thread
        self.asyncq = Queue()
        self.running = True
        self.trader = Thread(target=self.trader_background)
        self.trader.start()

        # quote updater thread
        self.pricer = Thread(target=self.price_updater)
        self.pricer.start()

    def price_updater(self):
        """
        Perform quote cache updating task
        """
        while self.running:
            self.log.info("price_updater")
            try:
                updatesym = None
                with closing(self.sql.getCursor()) as c:
                    row = c.execute("""SELECT * FROM stockplay_prices
                                        WHERE symbol in (SELECT symbol FROM stockplay_holdings WHERE count>0)
                                       ORDER BY time ASC LIMIT 1""").fetchone()
                    updatesym = row["symbol"] if row else None

                if updatesym:
                    self.get_price(updatesym, 0)

            except Exception:
                traceback.print_exc()
            delay = self.config["bginterval"]
            while self.running and delay > 0:
                delay -= 1
                sleep(1)

    def ondisable(self):
        self.running = False
        self.trader.join()
        self.pricer.join()

    def trader_background(self):
        """
        Perform trading, reporting and other background tasks
        """
        while self.running:
            try:
                queued = None
                try:
                    queued = self.asyncq.get(block=True, timeout=1)
                except Empty:
                    self.do_tasks()
                    continue
                if queued:
                    action, data = queued
                    if action == "trade":
                        self.do_trade(data)
                    elif action == "portreport":
                        self.do_report(*data)
                    elif action == "topten":
                        self.do_topten(*data)
            except Exception:
                traceback.print_exc()
                continue

    def do_topten(self, nick, replyto):
        """
        Do lookup of highest valued portfolios
        """
        self.log.warning("{} wants top 10 sent to {}".format(nick, replyto))

        with closing(self.sql.getCursor()) as c:
            for num, row in enumerate(c.execute("""SELECT h1.nick as nick, CAST(h1.cents as INTEGER) as cents FROM stockplay_balance_history h1
                                INNER JOIN (SELECT nick, max(day) as MaxDate FROM stockplay_balance_history WHERE nick != ? GROUP BY nick) h2
                                ON h1.nick = h2.nick AND h1.day = h2.MaxDate 
                                ORDER BY cents DESC LIMIT 10""", (DUSTACCT, )).fetchall(), start=1):
                total = Decimal(row.cents) / 100
                self.bot.act_PRIVMSG(replyto,
                                     "{}: {} with total: ~{}".format(num, row.nick, total), priority=5)

    def do_trade(self, trade):
        """
        Perform a queued trade
        """
        self.log.warning("{} wants to {} {} of {}".format(trade.nick,
                                                          "buy" if trade.buy else "sell",
                                                          trade.amount,
                                                          trade.symbol))
        # Update quote price
        try:
            symprice = self.get_price(trade.symbol, self.config["tcachesecs"])
        except Exception:
            traceback.print_exc()
            self.bot.act_PRIVMSG(trade.replyto, "{}: invalid symbol or api failure, trade aborted!"
                                                .format(trade.nick))
            return
        if symprice is None:
            self.bot.act_PRIVMSG(trade.replyto,
                                 "{}: invalid symbol '{}'".format(trade.nick, trade.symbol))
            return  # invalid stock

        # calculate various prices needed
        # symprice -= Decimal("0.0001")  # for testing dust collection
        dprice = symprice * trade.amount
        price_rounded = int(ceil(dprice * 100))  # now in cents
        dust = abs((dprice * 100) - price_rounded)  # cent fractions that we rounded out
        self.log.info("our price: {}".format(price_rounded))
        self.log.info("dust: {}".format(dust))

        # fetch existing user balances
        nickbal = self.get_bal(trade.nick)
        count = self.get_holding(trade.nick, trade.symbol)

        # check if trade is legal
        if trade.buy and nickbal < price_rounded:
            self.bot.act_PRIVMSG(trade.replyto, "{}: you can't afford {}."
                                 .format(trade.nick, format_price(price_rounded)))
            return  # can't afford trade
        if not trade.buy and trade.amount > count:
            self.bot.act_PRIVMSG(trade.replyto, "{}: you don't have that many.".format(trade.nick))
            return  # asked to sell more shares than they have

        # perform trade calculations
        if trade.buy:
            nickbal -= price_rounded
            count += trade.amount
        else:
            nickbal += price_rounded
            count -= trade.amount

        # commit the trade
        self.set_bal(trade.nick, nickbal)
        self.set_holding(trade.nick, trade.symbol, count)

        # save dust
        dustbal = self.get_bal(DUSTACCT)
        self.set_bal(DUSTACCT, dustbal + int(dust * 100))

        # notify user
        self.bot.act_PRIVMSG(trade.replyto,
                             "{}: {} {} {} for {}. cash: {}".format(trade.nick,
                                                                    "bought" if trade.buy else "sold",
                                                                    trade.amount,
                                                                    trade.symbol,
                                                                    format_price(price_rounded),
                                                                    format_price(nickbal)))

        self.log_trade(trade.nick, time(), "buy" if trade.buy else "sell",
                       trade.symbol, trade.amount, price_rounded)

    def do_report(self, lookup, sender, replyto, full):
        """
        Generate a text report of the nick's portfolio ::

            <@player> .port
            <bot> player: cash: $2,501.73 stock value: ~$7,498.27 total: ~$10,000.00
            <bot> player: 122xAMD=$2,812.10, 10xFB=$1,673.30, 10xJNUG=$108.80, 5xINTC=$244.20, ...
            <bot> player: 1xJD=$23.99, 1xMFGP=$19.78, 1xNOK=$6.16, 1xNVDA=$148.17, 1xTWTR=$30.01
        """
        data = self.build_report(lookup)
        dest = sender if full else replyto

        # Format holdings as "{symbol}x{price}={total_value}"
        sym_x_count = []
        for symbol, count, symprice in data["holdings"]:
            sym_x_count.append("{}x{}={}".format(count, symbol, format_decimal(symprice * count)))

        profit = data["24hgain"] >= 0
        gainloss = "(24h {}{} ({:,.2f}%){}\x0f)" \
                   .format("\x0303" if profit else "\x0304",  # green or red
                           format_decimal(data["24hgain"], prefix="", plus=True),
                           data["24hpct"] * 100,
                           "⬆" if profit else "⬇")

        self.bot.act_PRIVMSG(dest, "{}: {} cash: {} stock value: ~{} total: ~{} {}"
                             .format(sender,
                                     "you have" if lookup == sender else "{} has".format(lookup),
                                     format_decimal(data["cash"]),
                                     format_decimal(data["holding_value"]),
                                     format_decimal(data["cash"] + data["holding_value"]),
                                     gainloss))

        # print each symbol_count/total value with a max of 10 symbols per line
        while full and sym_x_count:
            message_segment = []
            for i in range(min(len(sym_x_count), 10)):  # show up to 10 "SYMx$d0llar, " strings per message
                message_segment.append(sym_x_count.pop(0))
            if sym_x_count:  # if there's more to print, append an ellipsis to indicate a forthcoming message
                message_segment.append("...")
            self.bot.act_PRIVMSG(dest, "{}: {}".format(sender, ", ".join(message_segment)))

    def build_report(self, nick):
        """
        Return a dict containing the player's cash, stock value, holdings listing, and 24 hour statistics.
        """
        cash = Decimal(self.get_bal(nick)) / 100

        # generate a list of (symbol, count, price) tuples of the player's holdings
        symbol_count = []
        holding_value = Decimal(0)
        with closing(self.sql.getCursor()) as c:
            for row in c.execute("SELECT * FROM stockplay_holdings WHERE count>0 AND nick=? ORDER BY count DESC",
                                 (nick, )).fetchall():
                # the API limits us to 5 requests per minute or 500 requests per day or about 1 request every 173s
                # The background thread updates the oldest price every 5 minutes. Here, we allow even very stale quotes
                # because it's simply impossible to request fresh data for every stock right now. Recommended rcachesecs
                # is 86400 (1 day)
                symprice = Decimal(self.get_price(row["symbol"], self.config["rcachesecs"]))
                holding_value += symprice * row["count"]
                symbol_count.append((row["symbol"], row["count"], symprice))

        # calculate gain/loss percent
        # TODO 1 week / 2 week / 1 month averages
        day_start_bal = self.get_latest_hist_bal(nick)
        gain_value = Decimal(0)
        gain_pct = Decimal(0)
        if day_start_bal:
            newbal = cash + holding_value
            startbal = Decimal(day_start_bal["cents"]) / 100
            gain_value = newbal - startbal
            gain_pct = gain_value / startbal

        return {"cash": cash,
                "holdings": symbol_count,
                "holding_value": holding_value,
                "24hgain": gain_value,
                "24hpct": gain_pct}

    def do_tasks(self):
        """
        Do interval tasks such as recording nightly balances
        """
        now = time()
        if now - 60 < self.task_time:
            return
        self.task_time = now
        self.record_nightly_balances()

    def get_price(self, symbol, thresh=None):
        """
        Get symbol price, with quote being at most $thresh seconds old
        """
        return self.get_priceinfo_cached(symbol, thresh or 60)["price"]

    def get_priceinfo_cached(self, symbol, thresh):
        """
        Return the cached symbol price if it's more recent than the last 15 minutes
        Otherwise, fetch the price then cache and return it.
        """
        cached = self._get_cache_priceinfo(symbol, thresh)
        if not cached:
            cached = self.fetch_priceinfo(symbol)
            if cached:
                self._set_cache_priceinfo(symbol, cached)

        numfields = set(['open', 'high', 'low', 'price', 'volume', 'change', 'previous close'])
        return {k: Decimal(v) if k in numfields else v for k, v in cached.items()}

    def _set_cache_priceinfo(self, symbol, data):
        with closing(self.sql.getCursor()) as c:
            c.execute("REPLACE INTO stockplay_prices VALUES (?, ?, ?)",
                      (symbol, time(), json.dumps(data)))

    def _get_cache_priceinfo(self, symbol, thresh):
        with closing(self.sql.getCursor()) as c:
            row = c.execute("SELECT * FROM stockplay_prices WHERE symbol=?",
                            (symbol, )).fetchone()
            if not row:
                return
            if time() - row["time"] > thresh:
                return
            return json.loads(row["data"])

    def fetch_priceinfo(self, symbol):
        """
        Request a stock quote from the API. The API provides the format::

            {'Global Quote': {
             {'01. symbol': 'MSFT',
              '02. open': '104.3900',
              '03. high': '105.7800',
              '04. low': '104.2603',
              '05. price': '105.6700',
              '06. volume': '21461093',
              '07. latest trading day':'2019-02-08',
              '08. previous close':'105.2700',
              '09. change': '0.4000',
              '10. change percent': '0.3800%'}}

        Reformat as::

            {'symbol': 'AMD',
             'open': '22.3300',
             'high': '23.2750',
             'low': '22.2700',
             'price': '23.0500',
             'volume': '78129280',
             'latest trading day': '2019-02-08',
             'previous close': '22.6700',
             'change': '0.3800',
             'change percent': '1.6762%'}
        """
        keys = set(['symbol', 'open', 'high', 'low', 'price', 'volume',
                    'latest trading day', 'previous close', 'change', 'change percent'])
        self.log.info("fetching api quote for symbol: {}".format(symbol))
        data = get("https://www.alphavantage.co/query",
                   params={"function": "GLOBAL_QUOTE",
                           "symbol": symbol,
                           "apikey": self.config["apikey"]},
                   timeout=10).json()
        data = data["Global Quote"]
        if not data:
            return None
        return {k[4:]: v for k, v in data.items() if k[4:] in keys}

    def checksym(self, s):
        """
        Validate that a string looks like a stock symbol
        """
        if len(s) > 12:
            return
        s = s.upper()
        if not RE_SYMBOL.match(s):
            return
        return s

    @info("buy <amount> <symbol>", "buy <amount> of stock <symbol>", cmds=["buy"])
    @command("buy", require_args=True, allow_private=True)
    @protected()
    def cmd_buy(self, message, command):
        """
        Command to buy stocks
        """
        self.check_nick(message.prefix.nick)
        amount = int(command.args[0])
        symbol = self.checksym(command.args[1])
        if not symbol or amount <= 0:
            return
        self.asyncq.put(("trade", Trade(message.prefix.nick,
                                        True,
                                        symbol,
                                        amount,
                                        message.args[0] if message.args[0].startswith("#") else message.prefix.nick)))

    @info("sell <amount> <symbol>", "buy <amount> of stock <symbol>", cmds=["sell"])
    @command("sell", require_args=True, allow_private=True)
    @protected()
    def cmd_sell(self, message, command):
        """
        Command to sell stocks
        """
        self.check_nick(message.prefix.nick)
        amount = int(command.args[0])
        symbol = self.checksym(command.args[1])
        if not symbol or amount <= 0:
            return
        self.asyncq.put(("trade", Trade(message.prefix.nick,
                                        False,
                                        symbol,
                                        amount,
                                        message.args[0] if message.args[0].startswith("#") else message.prefix.nick)))

    @info("port", "show portfolio holdings", cmds=["port", "portfolio"])
    @command("port", "portfolio", allow_private=True)
    @protected()
    def cmd_port(self, message, command):
        """
        Portfolio report command
        """
        full = False
        lookup = message.prefix.nick
        if command.args:
            if command.args[0] == "full":
                full = True
            else:
                lookup = command.args[0]
            if len(command.args) > 1 and command.args[1] == "full":
                full = True

        self.asyncq.put(("portreport", (lookup,
                                        message.prefix.nick,
                                        message.prefix.nick if full or not message.args[0].startswith("#")
                                        else message.args[0],
                                        full)))

    @info("top", "show top portfolios", cmds=["top", "top10"])
    @command("top", "top10", allow_private=True)
    def cmd_top(self, message, command):
        """
        Top 10 report command
        """
        self.asyncq.put(("topten", (message.prefix.nick,
                                    message.prefix.nick if not message.args[0].startswith("#") 
                                    else message.args[0])))

    def check_nick(self, nick):
        """
        Set up a user's account by setting the initial balance
        """
        if not self.nick_exists(nick):
            self.set_bal(nick, self.config["startbalance"] * 100)  # initial balance for user
            # TODO welcome message
            # TODO maybe even some random free shares for funzies

    def nick_exists(self, name):
        """
        Check whether a nick has a record
        """
        with closing(self.sql.getCursor()) as c:
            return c.execute("SELECT COUNT(*) as num FROM stockplay_balances WHERE nick=?",
                             (name, )).fetchone()["num"] and True

    def set_bal(self, nick, amount):
        """
        Set a player's balance
        :param amount: new balance in cents
        """
        with closing(self.sql.getCursor()) as c:
            c.execute("REPLACE INTO stockplay_balances VALUES (?, ?)",
                      (nick, amount, ))

    def get_bal(self, nick):
        """
        Get player's balance
        :return: balance in cents
        """
        with closing(self.sql.getCursor()) as c:
            return c.execute("SELECT * FROM stockplay_balances WHERE nick=?",
                             (nick, )).fetchone()["cents"]

    def get_holding(self, nick, symbol):
        """
        Return the number of stocks of a certain symbol a player has
        """
        assert symbol == symbol.upper()
        with closing(self.sql.getCursor()) as c:
            r = c.execute("SELECT * FROM stockplay_holdings WHERE nick=? AND symbol=?",
                          (nick, symbol, )).fetchone()
            return r["count"] if r else 0

    def set_holding(self, nick, symbol, count):
        """
        Set the number of stocks of a certain symbol a player that
        """
        with closing(self.sql.getCursor()) as c:
            c.execute("REPLACE INTO stockplay_holdings VALUES (?, ?, ?)",
                      (nick, symbol, count, ))

    def log_trade(self, nick, time, type, symbol, count, price):
        """
        Append a record of a trade to the database log
        """
        with closing(self.sql.getCursor()) as c:
            c.execute("INSERT INTO stockplay_trades VALUES (?, ?, ?, ?, ?, ?)",
                      (nick, time, type, symbol, count, price, ))

    def get_latest_hist_bal(self, nick):
        """
        Return the most recent historical balance of a player. Aka their "opening" value.
        """
        with closing(self.sql.getCursor()) as c:
            return c.execute("SELECT * FROM stockplay_balance_history WHERE nick=? ORDER BY DAY DESC LIMIT 1",
                             (nick, )).fetchone()

    def record_nightly_balances(self):
        """
        Create a record for each user's balance at the start of each day.
        """
        now = (datetime.now() + timedelta(seconds=self.config.get("midnight_offset", 0))).strftime("%Y-%m-%d")
        with closing(self.sql.getCursor()) as c:
            for row in c.execute("""SELECT * FROM stockplay_balances WHERE nick NOT IN
                                 (SELECT nick FROM stockplay_balance_history WHERE day=?)""", (now, )).fetchall():
                data = self.build_report(row["nick"])
                total = int((data["cash"] + data["holding_value"]) * 100)
                self.log.info("Recording {} daily balance for {}".format(now, row["nick"]))
                c.execute("INSERT INTO stockplay_balance_history VALUES (?, ?, ?)", (row["nick"], now, total))
