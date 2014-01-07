#!/usr/bin/env python
from modulebase import ModuleBase,ModuleHook
import sqlite3
import time

class Seen(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName)
		self.hooks=[ModuleHook("PRIVMSG", self.lastSeen)]
		self.loadConfig()
		# if the database doesnt exist, it will be created
		sql = self.getSql()
		c=sql.cursor()
		# check if our table exists
		c.execute("SELECT * FROM SQLITE_MASTER WHERE `type`='table' AND `name`='seen'")
		if len(c.fetchall())==0:
			self.log.info("Seen: Creating database")
			# if no, create it.
			c.execute("CREATE TABLE `seen` (`nick` VARCHAR(32), `date` INTEGER, PRIMARY KEY(`nick`))");
		self.x = "asdf"
	
	def lastSeen(self, args, prefix, trailing):
		# using a message to update last seen, also, the .seen query
		prefixObj = self.bot.decodePrefix(prefix)
		nick = prefixObj.nick
		sql=self.getSql()
		c = sql.cursor()
		# update or add the user's row
		datest=str( time.time()+(int(self.config["add_hours"])*60*60))
		c.execute("REPLACE INTO `seen` (`nick`, `date`) VALUES (?, ?)", (nick.lower(), datest ))
		self.log.info("Seen: %s on %s" % (nick.lower(), datest))
		sql.commit()
		if trailing.startswith(".seen"):
			cmdargs = trailing.split(" ");
			# query the DB for the user
			if len(cmdargs)>=2:
				searchnic = cmdargs[1].lower();
				c.execute("SELECT * FROM `seen` WHERE `nick`= ? ", [searchnic])
				rows = c.fetchall()
				if len(rows)==1:
					self.bot.act_PRIVMSG(args[0], "I last saw %s on %s (%s)."% (cmdargs[1], time.strftime("%m/%d/%y at %I:%M %p", time.localtime(rows[0]['date'])), self.config["timezone"]));
				else:
					self.bot.act_PRIVMSG(args[0], "Sorry, I haven't seen %s!" % cmdargs[1])
		c.close()
	
	def getSql(self):
		# return a SQL reference to the database
		path = self.getFilePath('database.sql3')
		sql = sqlite3.connect(path);
		sql.row_factory = self.dict_factory
		return sql
	
	def dict_factory(self, cursor, row):
		# because Lists suck for database results
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	
	def test(self, arg):
		print("TEST: %s" % arg)
		print("self.x = %s" % self.x)
		return arg
	
