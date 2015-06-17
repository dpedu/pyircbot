"""
.. module:: PyIRCBot
   :synopsis: Main IRC bot class

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import logging
import time
import sys
from core.rpc import BotRPC
from core.irccore import IRCCore
import os.path

class PyIRCBot:
	""":param coreconfig: The core configuration of the bot. Passed by main.py.
	:type coreconfig: dict
	:param botconfig: The configuration of this instance of the bot. Passed by main.py.
	:type botconfig: dict
	"""
	
	version = "1.0a1-git"
	""" PyIRCBot version """
	
	def __init__(self, coreconfig, botconfig):
		self.log = logging.getLogger('PyIRCBot')
		"""Reference to logger object"""
		
		self.coreconfig = coreconfig
		"""saved copy of the core config"""
		
		self.botconfig = botconfig
		"""saved copy of the instance config"""
		
		self.rpc = BotRPC(self)
		"""Reference to BotRPC thread"""
		
		self.irc = IRCCore()
		"""IRC protocol class"""
		self.irc.server = self.botconfig["connection"]["server"]
		self.irc.port = self.botconfig["connection"]["port"]
		self.irc.ipv6 = True if self.botconfig["connection"]["ipv6"]=="on" else False
		
		self.irc.addHook("_DISCONNECT", self.handle_close)
		
		# legacy support
		self.act_PONG = self.irc.act_PONG
		self.act_USER = self.irc.act_USER
		self.act_NICK = self.irc.act_NICK
		self.act_JOIN = self.irc.act_JOIN
		self.act_PRIVMSG = self.irc.act_PRIVMSG
		self.act_MODE = self.irc.act_MODE
		self.act_ACTION = self.irc.act_ACTION
		self.act_KICK = self.irc.act_KICK
		self.act_QUIT    = self.irc.act_QUIT
		self.get_nick    = self.irc.get_nick
		
		# Load modules 
		self.initModules()
		
		# Connect to IRC
		self.connect()
	
	def connect(self):
		self.irc._connect()
	
	def loop(self):
		self.irc.loop()
	
	def kill(self):
		"""Shut down the bot violently"""
		#Close all modules
		self.closeAllModules()
		
		self.irc.kill()
		
		sys.exit(0)
	
	
	" Net related code here on down "
	
	# TODO move handle_close to an event hook
	def handle_close(self):
		"""Called when the socket is disconnected. We will want to reconnect. """
		if self.alive:
			self.log.warning("Connection was lost. Reconnecting in 5 seconds.")
			time.sleep(5)
			self._connect()
	
	def initModules(self):
		"""load modules specified in instance config"""
		" storage of imported modules "
		self.modules = {}
		" instances of modules "
		self.moduleInstances = {}
		" append module location to path "
		sys.path.append(self.coreconfig["moduledir"])
		" append bot directory to path "
		sys.path.append(self.coreconfig["botdir"]+"core/")
		
		for modulename in self.botconfig["modules"]:
			self.loadmodule(modulename)
	
	def importmodule(self, name):
		"""Import a module
		
		:param moduleName: Name of the module to import
		:type moduleName: str"""
		" check if already exists "
		if not name in self.modules:
			" attempt to load "
			try:
				moduleref = __import__(name)
				self.modules[name]=moduleref
				return (True, None)
			except Exception as e:
				" on failure (usually syntax error in Module code) print an error "
				self.log.error("Module %s failed to load: " % name)
				self.log.error("Module load failure reason: " + str(e))
				return (False, str(e))
		else:
			self.log.warning("Module %s already imported" % name)
			return (False, "Module already imported")
	
	def deportmodule(self, name):
		"""Remove a module's code from memory. If the module is loaded it will be unloaded silently.
		
		:param moduleName: Name of the module to import
		:type moduleName: str"""
		" unload if necessary "
		if name in self.moduleInstances:
			self.unloadmodule(name)
		" delete all references to the module"
		if name in self.modules:
			item = self.modules[name]
			del self.modules[name]
			del item
			" delete copy that python stores in sys.modules "
			if name in sys.modules:
				del sys.modules[name]
	
	def loadmodule(self, name):
		"""Activate a module.
		
		:param moduleName: Name of the module to activate
		:type moduleName: str"""
		" check if already loaded "
		if name in self.moduleInstances:
			self.log.warning( "Module %s already loaded" % name )
			return False
		" check if needs to be imported, and verify it was "
		if not name in self.modules:
			importResult = self.importmodule(name)
			if not importResult[0]:
				return importResult
		" init the module "
		self.moduleInstances[name] = getattr(self.modules[name], name)(self, name)
		" load hooks "
		self.loadModuleHooks(self.moduleInstances[name])
	
	def unloadmodule(self, name):
		"""Deactivate a module.
		
		:param moduleName: Name of the module to deactivate
		:type moduleName: str"""
		if name in self.moduleInstances:
			" notify the module of disabling "
			self.moduleInstances[name].ondisable()
			" unload all hooks "
			self.unloadModuleHooks(self.moduleInstances[name])
			" remove the instance "
			item = self.moduleInstances.pop(name)
			" delete the instance"
			del item
			self.log.info( "Module %s unloaded" % name )
			return (True, None)
		else:
			self.log.info("Module %s not loaded" % name)
			return (False, "Module not loaded")
	
	def reloadmodule(self, name):
		"""Deactivate and activate a module.
		
		:param moduleName: Name of the target module
		:type moduleName: str"""
		" make sure it's imporeted"
		if name in self.modules:
			" remember if it was loaded before"
			loadedbefore = name in self.moduleInstances
			self.log.info("Reloading %s" % self.modules[name])
			" unload "
			self.unloadmodule(name)
			" load "
			if loadedbefore:
				self.loadmodule(name)
			return (True, None)
		return (False, "Module is not loaded")
	
	def redomodule(self, name):
		"""Reload a running module from disk
		
		:param moduleName: Name of the target module
		:type moduleName: str"""
		" remember if it was loaded before "
		loadedbefore = name in self.moduleInstances
		" unload/deport "
		self.deportmodule(name)
		" import "
		importResult = self.importmodule(name)
		if not importResult[0]:
			return importResult
		" load "
		if loadedbefore:
			self.loadmodule(name)
		return (True, None)
	
	def loadModuleHooks(self, module):
		"""**Internal.** Enable (connect) hooks of a module
		
		:param module: module object to hook in
		:type module: object"""
		" activate a module's hooks "
		for hook in module.hooks:
			if type(hook.hook) == list:
				for hookcmd in hook.hook:
					self.irc.addHook(hookcmd, hook.method)
			else:
				self.irc.addHook(hook.hook, hook.method)
	
	def unloadModuleHooks(self, module):
		"""**Internal.** Disable (disconnect) hooks of a module
		
		:param module: module object to unhook
		:type module: object"""
		" remove a modules hooks "
		for hook in module.hooks:
			if type(hook.hook) == list:
				for hookcmd in hook.hook:
					self.irc.removeHook(hookcmd, hook.method)
			else:
				self.irc.removeHook(hook.hook, hook.method)
	
	def getmodulebyname(self, name):
		"""Get a module object by name
		
		:param name: name of the module to return
		:type name: str
		:returns: object -- the module object"""
		if not name in self.moduleInstances:
			return None
		return self.moduleInstances[name]
	
	def getmodulesbyservice(self, service):
		"""Get a list of modules that provide the specified service 
		
		:param service: name of the service searched for
		:type service: str
		:returns: list -- a list of module objects"""
		validModules = []
		for module in self.moduleInstances:
			if service in self.moduleInstances[module].services:
				validModules.append(self.moduleInstances[module])
		return validModules
	
	def getBestModuleForService(self, service):
		"""Get the first module that provides the specified service 
		
		:param service: name of the service searched for
		:type service: str
		:returns: object -- the module object, if found. None if not found."""
		m = self.getmodulesbyservice(service)
		if len(m)>0:
			return m[0]
		return None
	
	def closeAllModules(self):
		""" Deport all modules (for shutdown). Modules are unloaded in the opposite order listed in the config. """
		loaded = list(self.moduleInstances.keys())
		loadOrder = self.botconfig["modules"]
		loadOrder.reverse()
		for key in loadOrder:
			if key in loaded:
				loaded.remove(key)
				self.deportmodule(key)
		for key in loaded:
			self.deportmodule(key)
	
	" Filesystem Methods "
	def getDataPath(self, moduleName):
		"""Return the absolute path for a module's data dir
		
		:param moduleName: the module who's data dir we want
		:type moduleName: str"""
		if not os.path.exists("%s/data/%s" % (self.botconfig["bot"]["datadir"], moduleName)):
			os.mkdir("%s/data/%s/" % (self.botconfig["bot"]["datadir"], moduleName))
		return "%s/data/%s/" % (self.botconfig["bot"]["datadir"], moduleName)
	
	def getConfigPath(self, moduleName):
		"""Return the absolute path for a module's config file
		
		:param moduleName: the module who's config file we want
		:type moduleName: str"""
		return "%s/config/%s.yml" % (self.botconfig["bot"]["datadir"], moduleName)
	
	" Utility methods "
	@staticmethod
	def messageHasCommand(command, message, requireArgs=False):
		"""Check if a message has a command with or without args in it
		
		:param command: the command string to look for, like !ban. If a list is passed, the first match is returned.
		:type command: str or list
		:param message: the message string to look in, like "!ban Lil_Mac"
		:type message: str
		:param requireArgs: if true, only validate if the command use has any amount of trailing text
		:type requireArgs: bool"""
		
		if not type(command)==list:
			command = [command]
		for item in command:
			cmd = PyIRCBot.messageHasCommandSingle(item, message, requireArgs)
			if cmd:
				return cmd
		return False
	
	@staticmethod
	def messageHasCommandSingle(command, message, requireArgs=False):
		# Check if the message at least starts with the command
		messageBeginning = message[0:len(command)]
		if messageBeginning!=command:
			return False
		# Make sure it's not a subset of a longer command (ie .meme being set off by .memes)
		subsetCheck = message[len(command):len(command)+1]
		if subsetCheck!=" " and subsetCheck!="":
			return False
		
		# We've got the command! Do we need args?
		argsStart = len(command)
		args = ""
		if argsStart > 0:
			args = message[argsStart+1:]
		
		if requireArgs and args.strip() == '':
			return False
		
		# Verified! Return the set.
		ob = type('ParsedCommand', (object,), {})
		ob.command = command
		ob.args = [] if args=="" else args.split(" ")
		ob.args_str = args
		ob.message = message
		return ob
		# return (True, command, args, message)
