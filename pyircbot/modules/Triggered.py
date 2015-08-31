#!/usr/bin/env python
"""
.. module::Triggered
    :synopsis: Scream when tirggered
.. moduleauthor::Dave Pedu <git@davepedu.com>
"""

from threading import Thread
from time import sleep,time
from pyircbot.modulebase import ModuleBase, ModuleHook
from random import randrange,choice

class Triggered(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.loadConfig()
        self.quietuntil = time()
        self.hooks.append(ModuleHook("PRIVMSG", self.check))

    def check(self, args):
        if time() < self.quietuntil:
            return
        if not args.args[0].lower() in self.config["channels"]:
            return
        
        message = args.trailing.lower()
        triggered = False
        for word in self.config["words"]:
            if word.lower() in message:
                triggered = True
                break
        
        if not triggered:
            return
        
        msg = Thread(target=self.scream, args=(args.args[0],))
        msg.daemon = True
        msg.start()
        
        self.quietuntil = time() + self.config["quiet"]

    def scream(self, channel):
        delay = randrange(self.config["mindelay"], self.config["maxdelay"])
        self.log.debug("Sleeping for %s seconds" % delay)
        sleep(delay)
        self.bot.act_PRIVMSG(channel, choice(self.config["responses"]))
