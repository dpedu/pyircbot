#!/ysr/bin/env python3

"""
.. module::LMGTFY
    :synopsis: LMGTFY
.. moduleauthor::Nick Krichevsky <nick@ollien.com>
"""

import urllib.parse
from pyircbot.modulebase import ModuleBase, ModuleHook

BASE_URL = "http://lmgtfy.com/?q="

class LMGTFY(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks.append(ModuleHook("PRIVMSG", self.handleMessage))
        self.bot = bot

    def handleMessage(self, args, prefix, trailing):
        channel = args[0]
        prefix = self.bot.decodePrefix(prefix)
        if self.bot.messageHasCommand(".lmgtfy", trailing):
            message = trailing.split(" ")[1:]
            link = self.createLink(message)
            self.bot.act_PRIVMSG(channel, "%s: %s" % (prefix.nick, link))
    
    def createLink(self, message):
        finalUrl = BASE_URL
        if type(message) == str:
            message = message.split(" ")

        for word in message:
            finalUrl += urllib.parse.quote(word)
            if word != message[-1]:
                finalUrl+="+"

        return finalUrl
