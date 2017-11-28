#!/usr/bin/env python
"""
.. module:: ServerPassword
    :synopsis: Allows connection to servers that require a password

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, hook


class ServerPassword(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)

    @hook("_CONNECT")
    def doConnect(self, msg, cmd):
        """Hook for when the IRC conneciton is opened"""
        if "password" in self.config and self.config["password"]:
            self.log.info("Sending server password")
            self.bot.act_PASS(self.config["password"])
