#!/usr/bin/env python
"""
.. module:: ServerPassword
    :synopsis: Allows connection to servers that require a password

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, ModuleHook


class ServerPassword(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks = [ModuleHook("_CONNECT", self.doConnect)]

    def doConnect(self, args, prefix, trailing):
        """Hook for when the IRC conneciton is opened"""
        if "password" in self.config and self.config["password"]:
            self.log.info("Sending server password")
            self.bot.act_PASS(self.config["password"])
