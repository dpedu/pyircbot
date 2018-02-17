#!/usr/bin/env python
"""
.. module:: PressF
    :synopsis: Press F to pay respects

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, hook
from time import sleep
from threading import Thread


class Rejoin(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        try:
            self._services = self.bot.getmodulesbyservice("services").pop()
        except KeyError as ke:
            raise Exception("No services service provider found") from ke

    @hook("KICK")
    def kicked(self, msg, cmd):
        channel, who = msg.args
        if who == self._services.nick():
            Thread(target=self.rejoin, args=(self.config.get("delay", 30), channel)).start()

    def rejoin(self, delay, channel):
        sleep(delay)
        self.bot.act_JOIN(channel)
