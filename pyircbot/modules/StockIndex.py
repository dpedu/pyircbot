from pyircbot.modulebase import ModuleBase, command
from pyircbot.modules.ModInfo import info
from threading import Thread
from time import sleep, time
import requests
import traceback


API_URL = "https://financialmodelingprep.com/api/v3/quotes/index?apikey={apikey}"


def bits(is_gain):
    if is_gain:
        return ("\x0303", "⬆", "+", )
    return ("\x0304", "⬇", "-", )


class StockIndex(ModuleBase):
    def __init__(self, bot, moduleName):
        super().__init__(bot, moduleName)
        self.session = requests.session()
        self.updater = None
        self.running = True
        self.last_update = 0
        self.start_cache_updater()

    def start_cache_updater(self):
        self.updater = Thread(target=self.cache_updater, daemon=True)
        self.updater.start()

    def ondisable(self):
        self.running = False
        self.updater.join()

    def cache_updater(self):
        while self.running:
            try:
                self.update_cache()
            except:
                traceback.print_exc()
            delay = self.config.get("cache_update_interval", 600)
            while self.running and delay > 0:
                delay -= 1
                sleep(1)

    def update_cache(self):
        data = self.session.get(API_URL.format(**self.config),
                                timeout=self.config.get("cache_update_timeout", 10)).json()
        self.cache = {item["symbol"]: item for item in data}
        self.last_update = time()

    @info("djia", "get the current value of the DJIA", cmds=["djia"])
    @command("djia", allow_private=True)
    def cmd_djia(self, message, command):
        self.send_quote("^DJI", "DJIA", message.replyto)

    @info("nasdaq", "get the current value of the NASDAQ composite index", cmds=["nasdaq"])
    @command("nasdaq", allow_private=True)
    def cmd_nasdaq(self, message, command):
        self.send_quote("^IXIC", "NASDAQ", message.replyto)

    def send_quote(self, key, symbol, to):
        index = self.cache[key]
        is_gain = index["price"] >= index["previousClose"]
        color, arrow, plusmin = bits(is_gain)

        change = float(index["price"]) - float(index["previousClose"])
        percentchange = float(change) / float(index["previousClose"]) * 100

        warn_thresh = self.config.get("warning_thresh", 1800)

        warning = "" if time() - self.last_update < warn_thresh else " \x030(quote is out-of-date)"

        self.bot.act_PRIVMSG(to, "{}{} ${:.2f} {}{:.2f} ({:.2f}%){}{}".format(color,
                                                                              symbol,
                                                                              index["price"],
                                                                              plusmin,
                                                                              change,
                                                                              percentchange,
                                                                              arrow,
                                                                              warning))
