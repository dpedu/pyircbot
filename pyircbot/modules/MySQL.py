#!/usr/bin/env python
from modulebase import ModuleBase,ModuleHook
import sys

try:
	import MySQLdb #python 2.x
except:
	import pymysql as MySQLdb #python 3.x

class MySQL(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[]
		self.services=["mysql"]
		self.loadConfig()
		self.connection = self.getConnection()
	
	def getConnection(self):
		return Connection(self)
	

class Connection:
	def __init__(self, master):
		self.config = master.config
		self.log = master.log
		self._connect()
	
	# Check if the table requested exists
	def tableExists(self, tablename):
		c = self.getCursor()
		c.execute("SHOW TABLES;")
		tables = c.fetchall()
		if len(tables)==0:
			return False;
		key = list(tables[0].keys())[0]
		for table in tables:
			if table[key]==tablename:
				return True;
		return False
	
	def query(self, queryText, args=()):
		c = self.getCursor()
		if len(args)==0:
			c.execute(queryText)
		else:
			c.execute(queryText, args)
		return c
	
	# Returns a cusor object, after checking for connectivity
	def getCursor(self):
		self.ensureConnected()
		if sys.version_info > (3,0):
			c = self.connection.cursor(MySQLdb.cursors.DictCursor)
		else:
			c = self.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		c.execute("USE `%s`;" % self.config["database"])
		return c
	
	def escape(self, s):
		self.ensureConnected()
		return self.connection.escape_string(s)
	
	def ensureConnected(self):
		try:
			self.connection.ping()
		except:
			try:
				self.connection.close()
			except:
				pass
			del self.connection
			self._connect()
	
	def ondisable(self):
		self.connection.close()
	
	# Connects to the database server, and selects a database (Or attempts to create it if it doesn't exist yet)
	def _connect(self):
		self.log.info("MySQL: Connecting to db host at %s" % self.config["host"])
		self.connection = MySQLdb.connect(host=self.config["host"],user=self.config["username"] ,passwd=self.config["password"])
		self.log.info("MySQL: Connected.")
		self.connection.autocommit(True)
		c = None
		if sys.version_info > (3,0):
			c = self.connection.cursor(MySQLdb.cursors.DictCursor)
		else:
			c = self.connection.cursor(cursorclass=MySQLdb.cursors.DictCursor)
		
		c.execute("SHOW DATABASES")
		dblist = c.fetchall()
		found = False
		for row in dblist:
			if row["Database"]==self.config["database"]:
				found = True
		if not found:
			c.execute("CREATE DATABASE `%s`;" % self.config["database"])
		c.execute("USE `%s`;" % self.config["database"])
		c.close()
