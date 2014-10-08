"""
.. module:: BotRPC
   :synopsis: RPC server

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import traceback
import logging
from core import jsonrpc
from threading import Thread

class BotRPC(Thread):
	def __init__(self, main):
		Thread.__init__(self, daemon=True)
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
		"""Internal, starts the RPC server"""
		self.server.serve()
	
	def importModule(self, moduleName):
		"""Import a module
		
		:param moduleName: Name of the module to import
		:type moduleName: str"""
		self.log.info("RPC: calling importModule(%s)"%moduleName)
		return self.bot.importmodule(moduleName)
	
	def deportModule(self, moduleName):
		"""Remove a module's code from memory. If the module is loaded it will be unloaded silently.
		
		:param moduleName: Name of the module to import
		:type moduleName: str"""
		self.log.info("RPC: calling deportModule(%s)"%moduleName)
		self.bot.deportmodule(moduleName)
	
	def loadModule(self, moduleName):
		"""Activate a module.
		
		:param moduleName: Name of the module to activate
		:type moduleName: str"""
		self.log.info("RPC: calling loadModule(%s)"%moduleName)
		return self.bot.loadmodule(moduleName)
	
	def unloadModule(self, moduleName):
		"""Deactivate a module.
		
		:param moduleName: Name of the module to deactivate
		:type moduleName: str"""
		self.log.info("RPC: calling unloadModule(%s)"%moduleName)
		self.bot.unloadmodule(moduleName)
	
	def reloadModule(self, moduleName):
		"""Deactivate and activate a module.
		
		:param moduleName: Name of the target module
		:type moduleName: str"""
		self.log.info("RPC: calling reloadModule(%s)"%moduleName)
		self.bot.unloadmodule(moduleName)
		return self.bot.loadmodule(moduleName)
	
	def redoModule(self, moduleName):
		"""Reload a running module from disk
		
		:param moduleName: Name of the target module
		:type moduleName: str"""
		self.log.info("RPC: calling redoModule(%s)"%moduleName)
		return self.bot.redomodule(moduleName)
	
	def getLoadedModules(self):
		"""Return a list of active modules
		
		:returns: list -- ['ModuleName1', 'ModuleName2']"""
		self.log.info("RPC: calling getLoadedModules()")
		return list(self.bot.moduleInstances.keys())
	
	def pluginCommand(self, moduleName, methodName, argList):
		"""Run a method of an active module
		
		:param moduleName: Name of the target module
		:type moduleName: str
		:param methodName: Name of the target method
		:type methodName: str
		:param argList: List of positional arguments to call the method with
		:type argList: list
		:returns: mixed -- Any basic type the target method may return"""
		plugin = self.bot.getmodulebyname(moduleName)
		if not plugin:
			return (False, "Plugin not found")
		method = getattr(plugin, methodName)
		if not method:
			return (False, "Method not found")
		self.log.info("RPC: calling %s.%s(%s)" % (moduleName, methodName, argList))
		return (True, method(*argList))
	
	def getPluginVar(self, moduleName, moduleVarName):
		"""Extract a property from an active module and return it
		
		:param moduleName: Name of the target module
		:type moduleName: str
		:param moduleVarName: Name of the target property
		:type moduleVarName: str
		:returns: mixed -- Any basic type extracted from an active module"""
		plugin = self.bot.getmodulebyname(moduleName)
		if moduleName == "_core":
			plugin = self.bot
		if not plugin:
			return (False, "Plugin not found")
		self.log.info("RPC: getting %s.%s" % (moduleName, moduleVarName))
		return (True, getattr(plugin, moduleVarName))
	
	def setPluginVar(self, moduleName, moduleVarName, value):
		"""Set a property of an active module
		
		:param moduleName: Name of the target module
		:type moduleName: str
		:param moduleVarName: Name of the target property
		:type moduleVarName: str
		:param value: Value the target property will be set to
		:type value: str"""
		plugin = self.bot.getmodulebyname(moduleName)
		if moduleName == "_core":
			plugin = self.bot
		if not plugin:
			return (False, "Plugin not found")
		self.log.info("RPC: setting %s.%s = %s )" % (moduleName, moduleVarName, value))
		setattr(plugin, moduleVarName, value)
		return (True, "Var set")
		
