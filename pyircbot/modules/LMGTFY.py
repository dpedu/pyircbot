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

    @info("lmgtfy <term>", "display a condescending internet query", cmds=["lmgtfy"])
    @command("lmgtfy", require_args=True)
    def handleMessage(self, msg, cmd):
        link = self.createLink(cmd.args_str)
        self.bot.act_PRIVMSG(msg.args[0], "{}: {}".format(msg.prefix.nick, link))

    def createLink(self, message):
        return BASE_URL + "+".join([urllib.parse.quote(word) for word in message.split()])
