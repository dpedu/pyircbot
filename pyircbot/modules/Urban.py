#!/usr/bin/env python
"""
.. module:: Urban
    :synopsis: Lookup from urban dictionary

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, command
import requests
from pyircbot.modules.ModInfo import info


class Urban(ModuleBase):

    @info("urban <term>      lookup an urban dictionary definition", cmds=["urban", "u"])
    @command("urban", "u")
    def urban(self, msg, cmd):
        definitions = requests.get("http://www.urbandictionary.com/iphone/search/define",
                                   params={"term": cmd.args_str}).json()["list"]
        if len(definitions) == 0:
            self.bot.act_PRIVMSG(msg.args[0], "Urban definition: no results!")
        else:
            defstr = definitions[0]['definition'].replace('\n', ' ').replace('\r', '')
            if len(defstr) > 360:
                defstr = defstr[0:360] + "..."
            self.bot.act_PRIVMSG(msg.args[0], "Urban definition: %s - http://urbanup.com/%s" %
                                 (defstr, definitions[0]['defid']))
