#!/ysr/bin/env python3

"""
.. module::LMGTFY
    :synopsis: LMGTFY
.. moduleauthor::Nick Krichevsky <nick@ollien.com>
"""

import urllib.parse
from pyircbot.modulebase import ModuleBase, command
from pyircbot.modules.ModInfo import info

BASE_URL = "http://lmgtfy.com/?q="


class LMGTFY(ModuleBase):

    @info("lmgtfy <term>     display a condescending internet query", cmds=["lmgtfy"])
    @command("lmgtfy", require_args=True)
    def handleMessage(self, msg, cmd):
        message = msg.trailing.split(" ")[1:]
        link = self.createLink(message)
        self.bot.act_PRIVMSG(msg.args[0], "%s: %s" % (msg.prefix.nick, link))

    def createLink(self, message):
        finalUrl = BASE_URL
        if type(message) == str:
            message = message.split(" ")

        for word in message:
            finalUrl += urllib.parse.quote(word)
            if word != message[-1]:
                finalUrl += "+"

        return finalUrl
