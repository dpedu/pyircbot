"""
.. module:: PyIRCBot
   :synopsis: Main IRC bot class

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import socket
import asynchat
import logging
import traceback
import time
import sys
from socket import SHUT_RDWR
from core.rpc import BotRPC
import os.path

try:
	from cStringIO import StringIO
except:
	from io import BytesIO as StringIO

class PyIRCBot(asynchat.async_chat):
	""":param coreconfig: The core configuration of the bot. Passed by main.py.
	:type coreconfig: dict
	:param botconfig: The configuration of this instance of the bot. Passed by main.py.
	:type botconfig: dict
	"""
	
	version = "1.0a1-git"
	""" PyIRCBot version """
	
	def __init__(self, coreconfig, botconfig):
		asynchat.async_chat.__init__(self)
		
		self.connected=False
		"""If we're connected or not"""
		
		self.log = logging.getLogger('PyIRCBot')
		"""Reference to logger object"""
		
		self.coreconfig = coreconfig
		"""saved copy of the core config"""
		
		self.botconfig = botconfig
		"""saved copy of the instance config"""
		
		self.rpc = BotRPC(self)
		"""Reference to BotRPC thread"""
		
		self.buffer = StringIO()
		"""cSTringIO used as a buffer"""
		
		self.alive = True
		""" True if we should try to stay connected"""
		
		# IRC Messages are terminated with \r\n
		self.set_terminator(b"\r\n")
		
		# Set up hooks for modules
		self.initHooks()
		
		# Load modules 
		self.initModules()
		
		# Connect to IRC
		self._connect()
	
	def kill(self):
		"""Shut down the bot violently"""
		#TODO: have rpc thread be daemonized so it just dies
		#try:
		#	self.rpc.server._Server__transport.shutdown(SHUT_RDWR)
		#except Exception as e:
		#	self.log.error(str(e))
		#try:
		#	self.rpc.server._Server__transport.close()
		#except Exception as e:
		#	self.log.error(str(e))
		
		#Kill RPC thread
		#self.rpc._stop()
		
		#Close all modules
		self.closeAllModules()
		# Mark for shutdown
		self.alive = False
		# Exit
		sys.exit(0)
	
	" Net related code here on down "
	
	def getBuf(self):
		"""Return the network buffer and clear it"""
		self.buffer.seek(0)
		data = self.buffer.read()
		self.buffer = StringIO()
		return data
	
	def collect_incoming_data(self, data):
		"""Recieve data from the IRC server, append it to the buffer
		
		:param data: the data that was recieved
		:type data: str"""
		#self.log.debug("<< %(message)s", {"message":repr(data)})
		self.buffer.write(data)
	
	def found_terminator(self):
		"""A complete command was pushed through, so clear the buffer and process it."""
		line = None
		buf = self.getBuf()
		try:
			line = buf.decode("UTF-8")
		except UnicodeDecodeError as ude:
			self.log.error("found_terminator(): could not decode input as UTF-8")
			self.log.error("found_terminator(): data: %s" % line)
			self.log.error("found_terminator(): repr(data): %s" % repr(line))
			self.log.error("found_terminator(): error: %s" % str(ude))
			return
		self.process_data(line)
	
	def handle_close(self):
		"""Called when the socket is disconnected. We will want to reconnect. """
		self.log.debug("handle_close")
		self.connected=False
		self.close()
		if self.alive:
			self.log.warning("Connection was lost. Reconnecting in 5 seconds.")
			time.sleep(5)
			self._connect()
	
	def handle_error(self, *args, **kwargs):
		"""Called on fatal network errors."""
		self.log.warning("Connection failed.")
	
	def _connect(self):
		"""Connect to IRC"""
		self.log.debug("Connecting to %(server)s:%(port)i", {"server":self.botconfig["connection"]["server"], "port":self.botconfig["connection"]["port"]})
		socket_type = socket.AF_INET
		if self.botconfig["connection"]["ipv6"]:
			self.log.info("IPv6 is enabled.")
			socket_type = socket.AF_INET6
		socketInfo = socket.getaddrinfo(self.botconfig["connection"]["server"], self.botconfig["connection"]["port"], socket_type)
		self.create_socket(socket_type, socket.SOCK_STREAM)
		if "bindaddr" in self.botconfig["connection"]:
			self.bind((self.botconfig["connection"]["bindaddr"], 0))
		self.connect(socketInfo[0][4])
	
	def handle_connect(self):
		"""When asynchat indicates our socket is connected, fire the connect hook"""
		self.connected=True
		self.log.debug("handle_connect: setting USER and NICK")
		self.fire_hook("_CONNECT")
		self.log.debug("handle_connect: complete")
	
	def sendRaw(self, text):
		"""Send a raw string to the IRC server
		
		:param text: the string to send
		:type text: str"""
		if self.connected:
			#self.log.debug(">> "+text)
			self.send( (text+"\r\n").encode("UTF-8").decode().encode("UTF-8"))
		else:
			self.log.warning("Send attempted while disconnected. >> "+text)
	
	def process_data(self, data):
		"""Process one line of tet irc sent us
		
		:param data: the data to process
		:type data: str"""
		if data.strip() == "":
			return
			
		prefix = None
		command = None
		args=[]
		trailing=None
		
		if data[0]==":":
			prefix=data.split(" ")[0][1:]
			data=data[data.find(" ")+1:]
		command = data.split(" ")[0]
		data=data[data.find(" ")+1:]
		if(data[0]==":"):
			# no args
			trailing = data[1:].strip()
		else:
			trailing = data[data.find(" :")+2:].strip()
			data = data[:data.find(" :")]
			args = data.split(" ")
		for index,arg in enumerate(args):
			args[index]=arg.strip()
		if not command in self.hookcalls:
			self.log.warning("Unknown command: cmd='%s' prefix='%s' args='%s' trailing='%s'" % (command, prefix, args, trailing))
		else:
			self.fire_hook(command, args=args, prefix=prefix, trailing=trailing)
	
	
	" Module related code "
	def initHooks(self):
		"""Defines hooks that modules can listen for events of"""
		self.hooks = [
			'_CONNECT', # Called when the bot connects to IRC on the socket level
			'NOTICE',	# :irc.129irc.com NOTICE AUTH :*** Looking up your hostname...
			'MODE',		# :CloneABCD MODE CloneABCD :+iwx
			'PING',		# PING :irc.129irc.com
			'JOIN',		# :CloneA!dave@hidden-B4F6B1AA.rit.edu JOIN :#clonea
			'QUIT',		# :HCSMPBot!~HCSMPBot@108.170.48.18 QUIT :Quit: Disconnecting!
			'NICK',		# :foxiAway!foxi@irc.hcsmp.com NICK :foxi
			'PART',		# :CloneA!dave@hidden-B4F6B1AA.rit.edu PART #clonea
			'PRIVMSG',	# :CloneA!dave@hidden-B4F6B1AA.rit.edu PRIVMSG #clonea :aaa
			'KICK',		# :xMopxShell!~rduser@host KICK #xMopx2 xBotxShellTest :xBotxShellTest
			'INVITE',	# :gmx!~gmxgeek@irc.hcsmp.com INVITE Tyrone :#hcsmp'
			'001',		# :irc.129irc.com 001 CloneABCD :Welcome to the 129irc IRC Network CloneABCD!CloneABCD@djptwc-laptop1.rit.edu
			'002',		# :irc.129irc.com 002 CloneABCD :Your host is irc.129irc.com, running version Unreal3.2.8.1
			'003',		# :irc.129irc.com 003 CloneABCD :This server was created Mon Jul 19 2010 at 03:12:01 EDT
			'004',		# :irc.129irc.com 004 CloneABCD irc.129irc.com Unreal3.2.8.1 iowghraAsORTVSxNCWqBzvdHtGp lvhopsmntikrRcaqOALQbSeIKVfMCuzNTGj
			'005',		# :irc.129irc.com 005 CloneABCD CMDS=KNOCK,MAP,DCCALLOW,USERIP UHNAMES NAMESX SAFELIST HCN MAXCHANNELS=10 CHANLIMIT=#:10 MAXLIST=b:60,e:60,I:60 NICKLEN=30 CHANNELLEN=32 TOPICLEN=307 KICKLEN=307 AWAYLEN=307 :are supported by this server
			'250',		# :chaos.esper.net 250 xBotxShellTest :Highest connection count: 1633 (1632 clients) (186588 connections received)
			'251',		# :irc.129irc.com 251 CloneABCD :There are 1 users and 48 invisible on 2 servers
			'252',		# :irc.129irc.com 252 CloneABCD 9 :operator(s) online
			'254',		# :irc.129irc.com 254 CloneABCD 6 :channels formed
			'255',		# :irc.129irc.com 255 CloneABCD :I have 42 clients and 1 servers
			'265',		# :irc.129irc.com 265 CloneABCD :Current Local Users: 42  Max: 47
			'266',		# :irc.129irc.com 266 CloneABCD :Current Global Users: 49  Max: 53
			'332',		# :chaos.esper.net 332 xBotxShellTest #xMopx2 :/ #XMOPX2 / https://code.google.com/p/pyircbot/ (Channel Topic)
			'333',		# :chaos.esper.net 333 xBotxShellTest #xMopx2 xMopxShell!~rduser@108.170.60.242 1344370109
			'353',		# :irc.129irc.com 353 CloneABCD = #clonea :CloneABCD CloneABC 
			'366',		# :irc.129irc.com 366 CloneABCD #clonea :End of /NAMES list.
			'372',		# :chaos.esper.net 372 xBotxShell :motd text here
			'375',		# :chaos.esper.net 375 xBotxShellTest :- chaos.esper.net Message of the Day -
			'376',		# :chaos.esper.net 376 xBotxShell :End of /MOTD command.
			'422',		# :irc.129irc.com 422 CloneABCD :MOTD File is missing
			'433',		# :nova.esper.net 433 * pyircbot3 :Nickname is already in use.
		]
		" mapping of hooks to methods "
		self.hookcalls = {}
		for command in self.hooks:
			self.hookcalls[command]=[]
	
	def fire_hook(self, command, args=None, prefix=None, trailing=None):
		"""Run any listeners for a specific hook
		
		:param command: the hook to fire
		:type command: str
		:param args: the list of arguments, if any, the command was passed
		:type args: list
		:param prefix: prefix of the sender of this command
		:type prefix: str
		:param trailing: data payload of the command
		:type trailing: str"""
		
		for hook in self.hookcalls[command]:
			try:
				hook(args, prefix, trailing)
			except:
				self.log.warning("Error processing hook: \n%s"% self.trace())
	
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
					self.addHook(hookcmd, hook.method)
			else:
				self.addHook(hook.hook, hook.method)
	
	def unloadModuleHooks(self, module):
		"""**Internal.** Disable (disconnect) hooks of a module
		
		:param module: module object to unhook
		:type module: object"""
		" remove a modules hooks "
		for hook in module.hooks:
			if type(hook.hook) == list:
				for hookcmd in hook.hook:
					self.removeHook(hookcmd, hook.method)
			else:
				self.removeHook(hook.hook, hook.method)
	
	def addHook(self, command, method):
		"""**Internal.** Enable (connect) a single hook of a module
		
		:param command: command this hook will trigger on
		:type command: str
		:param method: callable method object to hook in
		:type method: object"""
		" add a single hook "
		if command in self.hooks:
			self.hookcalls[command].append(method)
		else:
			self.log.warning("Invalid hook - %s" % command)
			return False
	
	def removeHook(self, command, method):
		"""**Internal.** Disable (disconnect) a single hook of a module
		
		:param command: command this hook triggers on
		:type command: str
		:param method: callable method that should be removed
		:type method: object"""
		" remove a single hook "
		if command in self.hooks:
			for hookedMethod in self.hookcalls[command]:
				if hookedMethod == method:
					self.hookcalls[command].remove(hookedMethod)
		else:
			self.log.warning("Invalid hook - %s" % command)
			return False
	
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
	def decodePrefix(prefix):
		"""Given a prefix like nick!username@hostname, return an object with these properties
		
		:param prefix: the prefix to disassemble
		:type prefix: str
		:returns: object -- an UserPrefix object with the properties `nick`, `username`, `hostname` or a ServerPrefix object with the property `hostname`"""
		if "!" in prefix:
			ob = type('UserPrefix', (object,), {})
			ob.nick, prefix = prefix.split("!")
			ob.username, ob.hostname = prefix.split("@")
			return ob
		else:
			ob = type('ServerPrefix', (object,), {})
			ob.hostname = prefix
			return ob
	
	@staticmethod
	def trace():
		"""Return the stack trace of the bot as a string"""
		return traceback.format_exc()
	
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
	
	
	" Data Methods "
	def get_nick(self):
		"""Get the bot's current nick
		
		:returns: str - the bot's current nickname"""
		return self.config["nick"]
	
	
	" Action Methods "
	def act_PONG(self, data):
		"""Use the `/pong` command - respond to server pings
		
		:param data: the string or number the server sent with it's ping
		:type data: str"""
		self.sendRaw("PONG :%s" % data)
	
	def act_USER(self, username, hostname, realname):
		"""Use the USER protocol command. Used during connection
		
		:param username: the bot's username
		:type username: str
		:param hostname: the bot's hostname
		:type hostname: str
		:param realname: the bot's realname
		:type realname: str"""
		self.sendRaw("USER %s %s %s :%s" % (username, hostname, self.botconfig["connection"]["server"], realname))
	
	def act_NICK(self, newNick):
		"""Use the `/nick` command
		
		:param newNick: new nick for the bot
		:type newNick: str"""
		self.sendRaw("NICK %s" % newNick)
	
	def act_JOIN(self, channel):
		"""Use the `/join` command
		
		:param channel: the channel to attempt to join
		:type channel: str"""
		self.sendRaw("JOIN %s"%channel)
	
	def act_PRIVMSG(self, towho, message):
		"""Use the `/msg` command
		
		:param towho: the target #channel or user's name
		:type towho: str
		:param message: the message to send
		:type message: str"""
		self.sendRaw("PRIVMSG %s :%s"%(towho,message))
	
	def act_MODE(self, channel, mode, extra=None):
		"""Use the `/mode` command
		
		:param channel: the channel this mode is for
		:type channel: str
		:param mode: the mode string. Example: +b
		:type mode: str
		:param extra: additional argument if the mode needs it. Example: user@*!*
		:type extra: str"""
		if extra != None:
			self.sendRaw("MODE %s %s %s" % (channel,mode,extra))
		else:
			self.sendRaw("MODE %s %s" % (channel,mode))
	
	def act_ACTION(self, channel, action):
		"""Use the `/me <action>` command
		
		:param channel: the channel name or target's name the message is sent to
		:type channel: str
		:param action: the text to send
		:type action: str"""
		self.sendRaw("PRIVMSG %s :\x01ACTION %s"%(channel,action))
	
	def act_KICK(self, channel, who, comment=""):
		"""Use the `/kick <user> <message>` command
		
		:param channel: the channel from which the user will be kicked
		:type channel: str
		:param who: the nickname of the user to kick
		:type action: str
		:param comment: the kick message
		:type comment: str"""
		self.sendRaw("KICK %s %s :%s" % (channel, who, comment))
	
	def act_QUIT(self, message):
		"""Use the `/quit` command
		
		:param message: quit message
		:type message: str"""
		self.sendRaw("QUIT :%s" % message)
	
