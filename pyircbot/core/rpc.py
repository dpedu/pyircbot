#!/usr/bin/env python
import traceback
import logging
from core import jsonrpc
from threading import Thread

class BotRPC(Thread):
	def __init__(self, main):
		Thread.__init__(self)
		self.bot = main
		self.log = logging.getLogger('RPC')
		self.server = jsonrpc.Server(jsonrpc.JsonRpc20(), jsonrpc.TransportTcpIp(addr=(self.bot.botconfig["bot"]["rpcbind"], self.bot.botconfig["bot"]["rpcport"])))
		
		self.server.register_function( self.importModule )
		self.server.register_function( self.deportModule )
		self.server.register_function( self.loadModule )
		self.server.register_function( self.unloadModule )
		self.server.register_function( self.reloadModule )
		self.server.register_function( self.redoModule )
		self.server.register_function( self.getTraceback )
		self.start()
	
	def run(self):
		self.server.serve()
	
	
	def importModule(self, moduleName):
		return self.bot.importmodule(moduleName)
	
	def deportModule(self, moduleName):
		self.bot.deportmodule(moduleName)
	
	def loadModule(self, moduleName):
		return self.bot.loadmodule(moduleName)
	
	def unloadModule(self, moduleName):
		self.bot.unloadmodule(moduleName)
	
	def reloadModule(self, moduleName):
		self.bot.unloadmodule(moduleName)
		return self.bot.loadmodule(moduleName)
	
	def redoModule(self, moduleName):
		return self.bot.redomodule(moduleName)
	
	def getTraceback(self):
		tb = str(traceback.format_exc())
		print(tb)
		return tb
	
	
	
