"""
.. module:: BitcoinPrice
    :synopsis: Provides .bitcoin to show price indexes

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, command
from pyircbot.modules.ModInfo import info
from decimal import Decimal
from requests import get
from time import time


class BitcoinPrice(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)

        self.cache = None
        self.cacheAge = 0

    @info("btc               retrieve the current price of bitcoin", cmds=["btc"])
    @command("btc", "bitcoin")
    def btc(self, msg, cmd):
        replyTo = msg.prefix.nick if "#" not in msg.args[0] else msg.args[0]

        data = self.getApi()
        self.bot.act_PRIVMSG(replyTo, "%s: %s" % (
            msg.prefix.nick,
            "\x02\x0307Bitcoin:\x03\x02 \x0307${price:.2f}\x0f - "
            "24h change: \x0307${change:.2f}\x0f - "
            "24h volume: \x0307${volume:.0f}M\x0f".format(price=Decimal(data["price_usd"]),
                                                          change=Decimal(data["percent_change_24h"]),
                                                          volume=Decimal(data["24h_volume_usd"]) / 10**6)
        ))

    def getApi(self):
        if self.cache is None or time() - self.cacheAge > self.config["cache"]:
            self.cache = get("https://api.coinmarketcap.com/v1/ticker/bitcoin/").json()[0]
            self.cacheAge = time()
        return self.cache
