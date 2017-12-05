#!/usr/bin/env python
"""
.. module:: PressF
    :synopsis: Press F to pay respects

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, regex
from time import time


class PressF(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.last = 0

    @regex(r'F', types=['PRIVMSG'], allow_private=False)
    def respect(self, msg, cmd):
        if time() - self.last > self.config.get("delay", 5):
            self.last = time()
            self.bot.act_PRIVMSG(msg.args[0], "F")
