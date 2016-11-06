#!/usr/bin/env python
"""
.. module:: AttributeStorage
    :synopsis: An item key->value storage engine based on mysql

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook

class AttributeStorage(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName);
        self.hooks=[]
        self.services=["attributes"]
        self.db = None
        serviceProviders = self.bot.getmodulesbyservice("mysql")
        if len(serviceProviders)==0:
            self.log.error("AttributeStorage: Could not find a valid mysql service provider")
        else:
            self.log.info("AttributeStorage: Selecting mysql service provider: %s" % serviceProviders[0])
            self.db = serviceProviders[0]
        
        if not self.db.connection.tableExists("attribute"):
            self.log.info("AttributeStorage: Creating table: attribute")
            c = self.db.connection.query("""CREATE TABLE IF NOT EXISTS `attribute` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `attribute` varchar(128) NOT NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `attribute` (`attribute`)
            ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ;""")
            c.close()
        
        if not self.db.connection.tableExists("items"):
            self.log.info("AttributeStorage: Creating table: items")
            c = self.db.connection.query("""CREATE TABLE IF NOT EXISTS `items` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `item` varchar(512) CHARACTER SET utf8 NOT NULL,
            PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ;""")
            c.close()
        
        if not self.db.connection.tableExists("values"):
            self.log.info("AttributeStorage: Creating table: values")
            c = self.db.connection.query("""CREATE TABLE IF NOT EXISTS `values` (
            `itemid` int(11) NOT NULL,
            `attributeid` int(11) NOT NULL,
            `value` varchar(512) CHARACTER SET utf8 NOT NULL,
            PRIMARY KEY (`itemid`,`attributeid`)
            ) ENGINE=InnoDB DEFAULT CHARSET=latin1 ;""")
            c.close()
        
        # self.getItem('xMopxShell', 'name')
        # self.getKey('xMopxShell', 'name')
        # self.setKey('xMopxShell', 'name', 'dave')
        
        # SELECT `i`.`id`, `i`.`item`, `a`.`attribute`, `v`.`value` FROM `items` `i` INNER JOIN `values` `v` on `v`.`itemid`=`i`.`id` INNER JOIN `attribute` `a` on `a`.`id`=`v`.`attributeid` ORDER BY `i`.`id` ASC, `a`.`id` ASC LIMIT 1000 ;
    
    def getItem(self, name):
        """Get all values for a item
        
        :param name: the item
        :type name: str
        :returns: dict -- the item's values expressed as a dict"""
        c = self.db.connection.query("""SELECT 
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
            `i`.`item`=%s;""",
            (name,)
        )
        item = {}
        while True:
            row = c.fetchone()
            if row == None:
                break
            item[row["attribute"]]=row["value"]
        c.close()
        
        if len(item)==0:
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
        c = self.db.connection.query("""SELECT 
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
            `i`.`item`=%s
                AND
            `a`.`attribute`=%s;""",
            (item,key)
        )
        row = c.fetchone()
        c.close()
        if row == None:
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
        c = self.db.connection.query("SELECT `id` FROM `attribute` WHERE `attribute`=%s;", (attribute))
        row = c.fetchone()
        attributeId = -1
        if row == None:
            c = self.db.connection.query("INSERT INTO `attribute` (`attribute`) VALUES (%s);", (attribute))
            attributeId = c.lastrowid
        else:
            attributeId = row["id"]
        c.close()
        
        # check item exists
        c = self.db.connection.query("SELECT `id` FROM `items` WHERE `item`=%s;", (item))
        row = c.fetchone()
        itemId = -1
        if row == None:
            c = self.db.connection.query("INSERT INTO `items` (`item`) VALUES (%s);", (item))
            itemId = c.lastrowid
        else:
            itemId = row["id"]
        c.close()
        
        if value == None:
            # delete it
            c = self.db.connection.query("DELETE FROM `values` WHERE `itemid`=%s AND `attributeid`=%s ;", (itemId, attributeId))
            self.log.info("AttributeStorage: Stored item %s attribute %s value: %s (Deleted)" % (itemId, attributeId, value))
        else:
            # add attribute
            c = self.db.connection.query("REPLACE INTO `values` (`itemid`, `attributeid`, `value`) VALUES (%s, %s, %s);", (itemId, attributeId, value))
            self.log.info("AttributeStorage: Stored item %s attribute %s value: %s" % (itemId, attributeId, value))
        c.close()
