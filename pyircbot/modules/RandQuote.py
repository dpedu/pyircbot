#!/usr/bin/env python
"""
.. module:: RandQuote
    :synopsis: Log a configurable number of messages and pull up random ones on command

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, ModuleHook
from datetime import datetime


class RandQuote(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks = []
        self.db = None
        serviceProviders = self.bot.getmodulesbyservice("sqlite")
        if not serviceProviders:
            self.log.error("RandQuote: Could not find a valid sqlite service provider")
        else:
            self.log.info("RandQuote: Selecting sqlite service provider: %s" % serviceProviders[0])
            self.db = serviceProviders[0].opendb("randquote.db")

        if not self.db.tableExists("chat"):
            self.log.info("RandQuote: Creating table: chat")
            c = self.db.query("""CREATE TABLE IF NOT EXISTS `chat` (
            `id` INTEGER PRIMARY KEY,
            `date` INTEGER,
            `sender` varchar(64),
            `message` varchar(2048)
            ) ;""")
            c.close()

        self.hooks = [ModuleHook("PRIVMSG", self.logquote),
                      ModuleHook("PRIVMSG", self.fetchquotes)]

    def fetchquotes(self, args, prefix, trailing):
        if not args[0][0] == "#":
            return
        cmd = self.bot.messageHasCommand([".randomquote", ".randquote", ".rq"], trailing)
        if cmd:
            c = self.db.query("SELECT * FROM `chat` ORDER BY RANDOM() LIMIT 1;")
            row = c.fetchone()
            c.close()
            if row:
                self.bot.act_PRIVMSG(args[0], "<%s> %s" % (row["sender"], row["message"],))

    def logquote(self, args, prefix, trailing):
        if not args[0][0] == "#":
            return
        prefixObj = self.bot.decodePrefix(prefix)
        self.db.query("INSERT INTO `chat` (`date`, `sender`, `message`) VALUES (?, ?, ?)",
                      (int(datetime.now().timestamp()), prefixObj.nick, trailing)).close()
        # Trim quotes
        c = self.db.query("SELECT * FROM `chat` ORDER BY `date` DESC LIMIT %s, 1000000;" % self.config["limit"])
        while True:
            row = c.fetchone()
            if not row:
                break
            self.db.query("DELETE FROM `chat` WHERE id=?", (row["id"],)).close()
        c.close()

    def ondisable(self):
        self.db.close()

