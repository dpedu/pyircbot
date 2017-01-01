#!/usr/bin/env python
"""
.. module:: Urban
    :synopsis: Lookup from urban dictionary

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, ModuleHook
from requests import get


class Urban(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks = [ModuleHook("PRIVMSG", self.urban)]

    def urban(self, args, prefix, trailing):
        cmd = self.bot.messageHasCommand(".urban", trailing)
        if not cmd:
            cmd = self.bot.messageHasCommand(".u", trailing)
        if cmd and args[0][0:1] == "#":
            if cmd.args_str.strip() == "":
                self.bot.act_PRIVMSG(args[0], ".u/.urban <phrase> -- looks up <phrase> on urbandictionary.com")
                return
            definitions = get("http://www.urbandictionary.com/iphone/search/define",
                              params={"term": cmd.args_str}).json()["list"]
            if len(definitions) == 0:
                self.bot.act_PRIVMSG(args[0], "Urban definition: no results!")
            else:
                defstr = definitions[0]['definition'].replace('\n', ' ').replace('\r', '')
                if len(defstr) > 360:
                    defstr = defstr[0:360] + "..."
                self.bot.act_PRIVMSG(args[0], "Urban definition: %s - http://urbanup.com/%s" %
                                     (defstr, definitions[0]['defid']))
