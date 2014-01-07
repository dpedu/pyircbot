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
		self.server.register_function( self.getLoadedModules )
		self.server.register_function( self.pluginCommand )
		self.server.register_function( self.setPluginVar )
		self.server.register_function( self.getPluginVar )
		
		self.start()
	
	def run(self):
		self.server.serve()
	
	def importModule(self, moduleName):
		self.log.info("RPC: calling importModule(%s)"%moduleName)
		return self.bot.importmodule(moduleName)
	
	def deportModule(self, moduleName):
		self.log.info("RPC: calling deportModule(%s)"%moduleName)
		self.bot.deportmodule(moduleName)
	
	def loadModule(self, moduleName):
		self.log.info("RPC: calling loadModule(%s)"%moduleName)
		return self.bot.loadmodule(moduleName)
	
	def unloadModule(self, moduleName):
		self.log.info("RPC: calling unloadModule(%s)"%moduleName)
		self.bot.unloadmodule(moduleName)
	
	def reloadModule(self, moduleName):
		self.log.info("RPC: calling reloadModule(%s)"%moduleName)
		self.bot.unloadmodule(moduleName)
		return self.bot.loadmodule(moduleName)
	
	def redoModule(self, moduleName):
		self.log.info("RPC: calling redoModule(%s)"%moduleName)
		return self.bot.redomodule(moduleName)
	
	def getLoadedModules(self):
		self.log.info("RPC: calling getLoadedModules()")
		return list(self.bot.moduleInstances.keys())
	
	def pluginCommand(self, pluginName, methodName, argList):
		plugin = self.bot.getmodulebyname(pluginName)
		if not plugin:
			return (False, "Plugin not found")
		method = getattr(plugin, methodName)
		if not method:
			return (False, "Method not found")
		self.log.info("RPC: calling %s.%s(%s)" % (pluginName, methodName, argList))
		return (True, method(*argList))
	
	def getPluginVar(self, pluginName, pluginVarName):
		plugin = self.bot.getmodulebyname(pluginName)
		if pluginName == "_core":
			plugin = self.bot
		if not plugin:
			return (False, "Plugin not found")
		self.log.info("RPC: getting %s.%s" % (pluginName, pluginVarName))
		return (True, getattr(plugin, pluginVarName))
	
	def setPluginVar(self, pluginName, pluginVarName, value):
		plugin = self.bot.getmodulebyname(pluginName)
		if pluginName == "_core":
			plugin = self.bot
		if not plugin:
			return (False, "Plugin not found")
		self.log.info("RPC: setting %s.%s = %s )" % (pluginName, pluginVarName, value))
		setattr(plugin, pluginVarName, value)
		return (True, "Var set")
		
