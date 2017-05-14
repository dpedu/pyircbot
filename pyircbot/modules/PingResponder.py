#!/usr/bin/env python
"""
.. module:: PingResponder
    :synopsis: Module to repsond to irc server PING requests

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from time import time, sleep
from threading import Thread
from pyircbot.modulebase import ModuleBase, ModuleHook


class PingResponder(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.timer = PingRespondTimer(self)
        self.hooks = [
            ModuleHook("PING", self.pingrespond),
            ModuleHook("_RECV", self.resettimer),
            ModuleHook("_SEND", self.resettimer)
        ]

    def pingrespond(self, args, prefix, trailing):
        """Respond to the PING command"""
        # got a ping? send it right back
        self.bot.act_PONG(trailing)
        self.log.info("%s Responded to a ping: %s" % (self.bot.get_nick(), trailing))

    def resettimer(self, msg):
        """Resets the connection failure timer"""
        self.timer.reset()

    def ondisable(self):
        self.timer.disable()


class PingRespondTimer(Thread):
    "Tracks last ping from server, and reconnects if over a threshold"
    def __init__(self, master):
        Thread.__init__(self)
        self.daemon = True
        self.alive = True
        self.master = master
        self.reset()
        self.start()

    def reset(self):
        "Reset the internal ping timeout counter"
        self.lastping = time()

    def disable(self):
        "Allow the thread to die"
        self.alive = False

    def run(self):
        while self.alive:
            sleep(5)
            if time() - self.lastping > self.config.get("activity_timeout", 300):
                self.master.log.info("No activity in %s seconds. Reconnecting" % str(time() - self.lastping))
                self.master.bot.disconnect("Reconnecting...")
                self.reset()

