#!/usr/bin/env python
"""
.. module:: AttributeStorageLite
    :synopsis: An item key->value storage engine based on Sqlite

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase


class AttributeStorageLite(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.services = ["attributes"]
        self.db = None
        serviceProviders = self.bot.getmodulesbyservice("sqlite")
        if len(serviceProviders) == 0:
            self.log.error("Could not find a valid sqlite service provider")
            raise Exception("No sqlite provider available")
        else:
            self.log.info("Selecting sqlite service provider: %s" % serviceProviders[0])
            self.db = serviceProviders[0].opendb("attributes.db")

        if not self.db.tableExists("attribute"):
            self.log.info("Creating table: attribute")
            c = self.db.query("""CREATE TABLE IF NOT EXISTS `attribute` (
            `id` INTEGER PRIMARY KEY,
            `attribute` varchar(128) UNIQUE
            ) ;""")
            c.close()

        if not self.db.tableExists("items"):
            self.log.info("Creating table: items")
            c = self.db.query("""CREATE TABLE IF NOT EXISTS `items` (
            `id` INTEGER PRIMARY KEY,
            `item` varchar(512)
            ) ;""")
            c.close()

        if not self.db.tableExists("values"):
            self.log.info("Creating table: values")
            c = self.db.query("""CREATE TABLE IF NOT EXISTS `values` (
            `itemid` INTEGER NOT NULL,
            `attributeid` INTEGER NOT NULL,
            `value` TEXT,
            PRIMARY KEY (`itemid`, `attributeid`)
            ) ;""")
            c.close()

    def getItem(self, name):
        """Get all values for a item

        :param name: the item
        :type name: str
        :returns: dict -- the item's values expressed as a dict"""
        c = self.db.query("""SELECT
            `i`.`id`,
            `i`.`item`,
            `a`.`attribute`,
            `v`.`value`
        FROM
            `items` `i`
                INNER JOIN `values` `v`
                    on `v`.`itemid`=`i`.`id`
                INNER JOIN `attribute` `a`
                    on `a`.`id`=`v`.`attributeid`

        WHERE
            `i`.`item`=?;""", (name.lower(),))
        item = {}
        while True:
            row = c.fetchone()
            if row is None:
                break
            item[row["attribute"]] = row["value"]
        c.close()

        if not item:
            return {}
        return item

    def get(self, item, key):
        return self.getKey(item, key)

    def getKey(self, item, key):
        """Get the value of an key on an item

        :param item: the item to fetch a key from
        :type item: str
        :param key: they key who's value to return
        :type key: str
        :returns: str -- the item from the database or **None**"""
        c = self.db.query("""SELECT
            `i`.`id`,
            `i`.`item`,
            `a`.`attribute`,
            `v`.`value`
        FROM
            `items` `i`
                INNER JOIN `values` `v`
                    on `v`.`itemid`=`i`.`id`
                INNER JOIN `attribute` `a`
                    on `a`.`id`=`v`.`attributeid`

        WHERE
            `i`.`item`=?
                AND
            `a`.`attribute`=?;""", (item.lower(), key.lower()))
        row = c.fetchone()

        c.close()
        if row is None:
            return None
        return row["value"]

    def set(self, item, key, value):
        return self.setKey(item, key, value)

    def setKey(self, item, key, value):
        """Set the key on an item

        :param item: the item name to set the key on
        :type item: str
        :param key: the key to set
        :type key: tuple
        :param value: the value to set
        :type value: str"""
        item = item.lower()
        attribute = key.lower()

        # Check attribute exists
        c = self.db.query("SELECT `id` FROM `attribute` WHERE `attribute`=?;", (attribute,))
        row = c.fetchone()
        attributeId = -1
        if row is None:
            c = self.db.query("INSERT INTO `attribute` (`attribute`) VALUES (?);", (attribute,))
            attributeId = c.lastrowid
        else:
            attributeId = row["id"]
        c.close()

        # check item exists
        c = self.db.query("SELECT `id` FROM `items` WHERE `item`=?;", (item,))
        row = c.fetchone()
        itemId = -1
        if row is None:
            c = self.db.query("INSERT INTO `items` (`item`) VALUES (?);", (item,))
            itemId = c.lastrowid
        else:
            itemId = row["id"]
        c.close()

        if value is None:
            # delete it
            c = self.db.query("DELETE FROM `values` WHERE `itemid`=? AND `attributeid`=? ;", (itemId, attributeId))
            self.log.info("Stored item %s attribute %s value: %s (Deleted)" % (itemId, attributeId, value))
        else:
            c = self.db.query("REPLACE INTO `values` (`itemid`, `attributeid`, `value`) VALUES (?, ?, ?);",
                              (itemId, attributeId, value))
            self.log.info("Stored item %s attribute %s value: %s" % (itemId, attributeId, value))
        c.close()
