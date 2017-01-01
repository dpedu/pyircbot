"""
.. module:: BitcoinPrice
    :synopsis: Provides .bitcoin to show price indexes

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, ModuleHook
from requests import get
from time import time


class BitcoinPrice(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)

        self.cache = None
        self.cacheAge = 0

        self.hooks = [
            ModuleHook(["PRIVMSG"], self.btc)
        ]

    def btc(self, args, prefix, trailing):
        prefix = self.bot.decodePrefix(prefix)
        replyTo = prefix.nick if "#" not in args[0] else args[0]

        cmd = self.bot.messageHasCommand([".btc", ".bitcoin"], trailing)
        if cmd:
            data = self.getApi()
            self.bot.act_PRIVMSG(replyTo, "%s: %s" % (
                prefix.nick,
                "\x02\x0307Bitcoin:\x03\x02 \x0307{buy:.0f}\x0f$ - High: \x0307{high:.0f}\x0f$ - "
                "Low: \x0307{low:.0f}\x0f$ - Volume: \x0307{vol_cur:.0f}\x03฿".format(**data['ticker'])
            ))

    def getApi(self):
        if self.cache is None or time() - self.cacheAge > self.config["cache"]:
            self.cache = get("https://btc-e.com/api/2/btc_usd/ticker").json()
            self.cacheAge = time()
        return self.cache
