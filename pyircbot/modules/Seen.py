#!/usr/bin/env python
"""
.. module:: Seen
    :synopsis: Provides !seen <username>

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modules.ModInfo import info
from pyircbot.modulebase import ModuleBase, command, hook
from contextlib import closing
import sqlite3
import time


class Seen(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        # if the database doesnt exist, it will be created
        sql = self.getSql()
        c = sql.cursor()
        # check if our table exists
        c.execute("SELECT * FROM SQLITE_MASTER WHERE `type`='table' AND `name`='seen'")
        if len(c.fetchall()) == 0:
            self.log.info("Seen: Creating database")
            # if no, create it.
            c.execute("CREATE TABLE `seen` (`nick` VARCHAR(32), `date` INTEGER, PRIMARY KEY(`nick`))")
        self.x = "asdf"

    @hook("PRIVMSG")
    def recordSeen(self, message, command):
        # using a message to update last seen, also, the .seen query
        datest = str(time.time() + (int(self.config["add_hours"]) * 60 * 60))
        sql = self.getSql()
        with closing(sql.cursor()) as c:
            # update or add the user's row
            c.execute("REPLACE INTO `seen` (`nick`, `date`) VALUES (?, ?)", (message.prefix.nick.lower(), datest))
            # self.log.info("Seen: %s on %s" % (nick.lower(), datest))
            sql.commit()

    @info("seen <nick>       print last time user was seen", cmds=["seen"])
    @command("seen", require_args=True)
    def lastSeen(self, message, command):
        sql = self.getSql()
        searchnic = command.args[0].lower()
        with closing(sql.cursor()) as c:
            # query the DB for the user
            c.execute("SELECT * FROM `seen` WHERE `nick`= ? ", [searchnic])
            rows = c.fetchall()
            if len(rows) == 1:
                self.bot.act_PRIVMSG(message.args[0], "I last saw %s on %s (%s)." %
                                     (command.args[0], time.strftime("%m/%d/%y at %I:%M %p",
                                      time.localtime(rows[0]['date'])), self.config["timezone"]))
            else:
                self.bot.act_PRIVMSG(message.args[0], "Sorry, I haven't seen %s!" % command.args[0])

    def getSql(self):
        # return a SQL reference to the database
        path = self.getFilePath('database.sql3')
        sql = sqlite3.connect(path)
        sql.row_factory = self.dict_factory
        return sql

    def dict_factory(self, cursor, row):
        # because Lists suck for database results
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
