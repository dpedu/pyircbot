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
import re
import json
import traceback


RE_SYMBOL = re.compile(r'^([A-Z\-]+)$')
DUSTACCT = "#dust"

Trade = namedtuple("Trade", "nick buy symbol amount replyto")


def format_price(cents):
    return "${:,.2f}".format(Decimal(cents) / 100)


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

        # trade executor thread
        self.asyncq = Queue()
        self.running = True
        self.trader = Thread(target=self.trader_background)
        self.trader.start()

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
        Perform trading and reporting tasks
        """
        while self.running:
            try:
                self.do_background()
            except Exception:
                traceback.print_exc()
                continue

    def do_background(self):
        queued = None
        try:
            queued = self.asyncq.get(block=True, timeout=1)
        except Empty:
            return
        if not queued:
            return

        action, data = queued

        if action == "trade":
            # Perform a stock trade
            trade = data
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
            # print("that would cost ", repr(dprice))
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

        elif action == "portreport":
            # Generate a text report of the nick's portfolio
            # <@player> .port
            # <bot> player: cash: $2,501.73 stock value: ~$7,498.27 total: ~$10,000.00
            # <bot> player: 122xAMD=$2,812.10, 10xFB=$1,673.30, 10xJNUG=$108.80, 5xINTC=$244.20, ...
            # <bot> player: 1xJD=$23.99, 1xMFGP=$19.78, 1xNOK=$6.16, 1xNVDA=$148.17, 1xTWTR=$30.01
            lookup, sender, replyto, full = data
            cash = self.get_bal(lookup)
            # when $full is true we PM the user instead
            # when $full is false we just say their total value

            # generate a list of (symbol, count, ) tuples of the player's symbol holdings
            symbol_count = []
            with closing(self.sql.getCursor()) as c:
                for row in c.execute("SELECT * FROM stockplay_holdings WHERE count>0 AND nick=? ORDER BY count DESC",
                                     (lookup, )).fetchall():
                    symbol_count.append((row["symbol"], row["count"], ))

            # calculate the cash sum of the player's symbol holdings (while also formatting text representations)
            sym_x_count = []
            stock_value = Decimal(0)
            for symbol, count in symbol_count:
                # the API limits us to 5 requests per minute or 500 requests per day or about 1 request every 173s
                # The background thread updates the oldest price every 5 minutes. Here, we allow even very stale quotes
                # because it's simply impossible to request fresh data for every stock right now. Recommended rcachesecs
                # is 86400 (1 day)
                symprice = self.get_price(symbol, self.config["rcachesecs"])
                dprice = Decimal(symprice * count) * 100
                stock_value += dprice
                sym_x_count.append("{}x{}={}".format(count, symbol, format_price(dprice)))

            dest = sender if full else replyto

            self.bot.act_PRIVMSG(dest, "{}: {} cash: {} stock value: ~{} total: ~{}"
                                 .format(sender,
                                         "you have" if lookup == sender else "{} has".format(lookup),
                                         format_price(cash),
                                         format_price(stock_value),
                                         format_price(cash + stock_value)))
            if full:
                # print symbol_count with a max of 10 symbols per line
                while sym_x_count:
                    message_segment = []
                    for i in range(min(len(sym_x_count), 10)):  # show up to 10 "SYMx$d0llar, " strings per message
                        message_segment.append(sym_x_count.pop(0))
                    if sym_x_count:  # if there's more to print, append an ellipsis to indicate a forthcoming message
                        message_segment.append("...")
                    self.bot.act_PRIVMSG(dest, "{}: {}".format(sender, ", ".join(message_segment)))

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
        API provides
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
        Reformat as:
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

    def check_nick(self, nick):
        if not self.nick_exists(nick):
            self.set_bal(nick, self.config["startbalance"] * 100)  # initial balance for user
            # TODO welcome message
            # TODO maybe even some random free shares for funzies

    def nick_exists(self, name):
        with closing(self.sql.getCursor()) as c:
            return c.execute("SELECT COUNT(*) as num FROM stockplay_balances WHERE nick=?",
                             (name, )).fetchone()["num"] and True

    def set_bal(self, nick, amount):
        with closing(self.sql.getCursor()) as c:
            c.execute("REPLACE INTO stockplay_balances VALUES (?, ?)",
                      (nick, amount, ))

    def get_bal(self, nick):
        with closing(self.sql.getCursor()) as c:
            return c.execute("SELECT * FROM stockplay_balances WHERE nick=?",
                             (nick, )).fetchone()["cents"]

    def get_holding(self, nick, symbol):
        assert symbol == symbol.upper()
        with closing(self.sql.getCursor()) as c:
            r = c.execute("SELECT * FROM stockplay_holdings WHERE nick=? AND symbol=?",
                          (nick, symbol, )).fetchone()
            return r["count"] if r else 0

    def set_holding(self, nick, symbol, count):
        with closing(self.sql.getCursor()) as c:
            c.execute("REPLACE INTO stockplay_holdings VALUES (?, ?, ?)",
                      (nick, symbol, count, ))

    def log_trade(self, nick, time, type, symbol, count, price):
        with closing(self.sql.getCursor()) as c:
            c.execute("INSERT INTO stockplay_trades VALUES (?, ?, ?, ?, ?, ?)",
                      (nick, time, type, symbol, count, price, ))
