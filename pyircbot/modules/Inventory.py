#!/usr/bin/env python
"""
.. module:: Inventory
    :synopsis: Lets the bot hold random items

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, command
from pyircbot.modules.ModInfo import info
from datetime import datetime


class Inventory(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.db = None
        serviceProviders = self.bot.getmodulesbyservice("sqlite")
        if not serviceProviders:
            self.log.error("Inventory: Could not find a valid sqlite service provider")
        else:
            self.log.info("Inventory: Selecting sqlite service provider: %s" % serviceProviders[0])
            self.db = serviceProviders[0].opendb("inventory.db")

        if not self.db.tableExists("inventory"):
            self.log.info("Inventory: Creating table: inventory")
            c = self.db.query("""CREATE TABLE IF NOT EXISTS `inventory` (
            `id` INTEGER PRIMARY KEY,
            `date` INTEGER,
            `donor` varchar(64),
            `item` varchar(64)
            ) ;""")
            c.close()

    @info("have <item>       give the bot an item", cmds=["have"])
    @command("have")
    def checkInv(self, msg, cmd):
        if len(cmd.args) < 1:
            return
        adjective = None
        newItem = cmd.args_str
        if cmd.args[0] in self.config["adjectives"]:
            newItem = cmd.args_str[len(cmd.args[0]):].strip()
            adjective = cmd.args[0]

        if self.has_item(newItem):
            self.bot.act_PRIVMSG(msg.args[0], self.config["dupe_msg"] % {"item": newItem})
            return

        dropped = self.add_item(msg.prefix.nick, newItem)
        if len(dropped) > 0:
            self.bot.act_PRIVMSG(msg.args[0], self.config["swap_msg"] %
                                 {"adjective": (adjective + " ") if adjective else "",
                                  "recv_item": newItem, "drop_item": ", ".join(dropped)})
        else:
            self.bot.act_PRIVMSG(msg.args[0], self.config["recv_msg"] %
                                 {"item": newItem, "adjective": "these " if newItem[-1:] == "s" else "this "})

    @info("inventory         show the bot's inventory", cmds=["inventory", "inv"])
    @command("inventory", "inv")
    def cmd_inv(self, msg, cmd):
        inv = self.getinventory()
        if len(inv) == 0:
            self.bot.act_PRIVMSG(msg.args[0], self.config["inv_msg"] % {"itemlist": "nothing!"})
        else:
            self.bot.act_PRIVMSG(msg.args[0], self.config["inv_msg"] % {"itemlist": ", ".join(inv)})

    def has_item(self, itemName):
        c = self.db.query("SELECT COUNT(*) as `num` FROM `inventory` WHERE `item`=? COLLATE NOCASE", (itemName,))
        row = c.fetchone()
        c.close()
        return row["num"] > 0

    def add_item(self, donor, itemName):
        dropped = []
        c = self.db.query("SELECT * FROM `inventory` ORDER BY RANDOM() LIMIT %s,1000000" % self.config["limit"])
        while True:
            row = c.fetchone()
            if row is None:
                break
            dropped.append(row["item"])
            self.db.query("DELETE FROM `inventory` WHERE `id`=?", (row["id"],)).close()
        c.close()

        self.db.query("INSERT INTO `inventory` (`date`, `donor`, `item`) VALUES (?, ?, ?)",
                      (int(datetime.now().timestamp()), donor, itemName)).close()
        return dropped

    def getinventory(self):
        inv = []
        c = self.db.query("SELECT * FROM `inventory`")
        while True:
            row = c.fetchone()
            if row is None:
                break
            inv.append(row["item"])
        c.close()
        return inv

    def ondisable(self):
        self.db.close()

