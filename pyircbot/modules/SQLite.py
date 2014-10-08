#!/usr/bin/env python
"""
.. module:: SQLite
	:synopsis: Module providing a sqlite type service

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from modulebase import ModuleBase
import sys
import sqlite3

class SQLite(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[]
		self.services=["sqlite"]
		self.loadConfig()
	
	def opendb(self, dbname):
		return Connection(self, dbname)
	

class Connection:
	def __init__(self, master, dbname):
		self.master = master
		self.log = master.log
		self.dbname = dbname
		self.connection = None
		self._connect()
	
	# Check if the table requested exists
	def tableExists(self, tablename):
		c = self.getCursor()
		c.execute("SELECT * FROM SQLITE_MASTER WHERE `type`='table' AND `name`=?", (tablename,))
		tables = c.fetchall()
		if len(tables)==0:
			return False;
		return True
	
	@staticmethod
	def dict_factory(cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d

	def query(self, queryText, args=()):
		"""Execute a Sqlite query and return the cursor
		
		:param queryText: the sqlite query as a string, using '%s' for token replacement
		:type queryText: str
		:param args: arguments to be escaped into the query
		:type args: tuple
		:returns: cursor -- the sql cursor"""
		c = self.getCursor()
		if len(args)==0:
			c.execute(queryText)
		else:
			c.execute(queryText, args)
		return c
	
	# Returns a cusor object, after checking for connectivity
	def getCursor(self):
		c=self.connection.cursor()
		return c
	
	def escape(self, s):
		raise NotImplementedError
	
	def ondisable(self):
		self.connection.close()
	
	# Connects to the database server, and selects a database (Or attempts to create it if it doesn't exist yet)
	def _connect(self):
		self.log.info("Sqlite: opening database %s" % self.master.getFilePath(self.dbname))
		self.connection = sqlite3.connect(self.master.getFilePath(self.dbname))
		self.connection.row_factory = Connection.dict_factory
		self.connection.isolation_level = None
		self.log.info("Sqlite: Connected.")
		
		# Test the connection
		c = self.connection.cursor()
		derp=c.execute("SELECT * FROM SQLITE_MASTER")
		c.close()
