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
	
	def __init__(self, coreconfig, botconfig):
		asynchat.async_chat.__init__(self)
		
		self.log = logging.getLogger('PyIRCBot')
		"""Reference to logger object"""
		
		self.coreconfig = coreconfig
		"""saved copy of the core config"""
		
		self.botconfig = botconfig
		"""saved copy of the instance config"""
		
		" rpc "
		self.rpc = BotRPC(self)
		
		" stringio object as buffer "
		self.buffer = StringIO()
		" line terminator "
		self.set_terminator(b"\r\n")
		
		" Setup hooks for modules "
		self.initHooks()
		" Load modules "
		self.initModules()
		
		self._connect()
		self.connected=False
	
	def kill(self):
		" Close RPC Socket "
		#try:
		#	self.rpc.server._Server__transport.shutdown(SHUT_RDWR)
		#except Exception as e:
		#	self.log.error(str(e))
		try:
			self.rpc.server._Server__transport.close()
		except Exception as e:
			self.log.error(str(e))
		
		" Kill RPC thread "
		self.rpc._stop()
		
		" Close all modules "
		self.closeAllModules()
	
	" Net related code "
	
	def getBuf(self):
		" return buffer and clear "
		self.buffer.seek(0)
		data = self.buffer.read()
		self.buffer = StringIO()
		return data
	
	def collect_incoming_data(self, data):
		" Recieve data from stream, add to buffer "
		self.log.debug("<< %(message)s", {"message":repr(data)})
		self.buffer.write(data)
	
	def found_terminator(self):
		" A complete command was pushed through, so clear the buffer and process it."
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
		" called on socket shutdown "
		self.log.debug("handle_close")
		self.connected=False
		self.close()
		
		self.log.warning("Connection was lost. Reconnecting in 5 seconds.")
		time.sleep(5)
		self._connect()
	
	def handle_error(self, *args, **kwargs):
		self.log.warning("Connection failed.")
	
	def _connect(self):
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
		" Called when the first packets come through, so we ident here "
		self.connected=True
		self.log.debug("handle_connect: setting USER and NICK")
		self.fire_hook("_CONNECT")
		self.log.debug("handle_connect: complete")
	
	def sendRaw(self, text):
		if self.connected:
			self.log.debug(">> "+text)
			self.send( (text+"\r\n").encode("ascii"))
		else:
			self.log.warning("Send attempted while disconnected. >> "+text)
	
	def process_data(self, data):
		" called per line of irc sent through "
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
		for hook in self.hookcalls[command]:
			try:
				hook(args, prefix, trailing)
			except:
				self.log.warning("Error processing hook: \n%s"% self.trace())
	
	def initModules(self):
		" load modules specified in config "
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
		" import a module by name "
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
		" remove a module from memory by name "
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
		" load a module and activate it "
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
		" unload a module by name "
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
		" unload then load a module by name "
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
		" reload a modules code from disk "
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
		" activate a module's hooks "
		for hook in module.hooks:
			self.addHook(hook.hook, hook.method)
	
	def unloadModuleHooks(self, module):
		" remove a modules hooks "
		for hook in module.hooks:
			self.removeHook(hook.hook, hook.method)
	
	def addHook(self, command, method):
		" add a single hook "
		if command in self.hooks:
			self.hookcalls[command].append(method)
		else:
			self.log.warning("Invalid hook - %s" % command)
			return False
	
	def removeHook(self, command, method):
		" remove a single hook "
		if command in self.hooks:
			for hookedMethod in self.hookcalls[command]:
				if hookedMethod == method:
					self.hookcalls[command].remove(hookedMethod)
		else:
			self.log.warning("Invalid hook - %s" % command)
			return False
	
	def getmodulebyname(self, name):
		" return a module specified by the name "
		if not name in self.moduleInstances:
			return None
		return self.moduleInstances[name]
	
	def getmodulesbyservice(self, service):
		" get a list of modules that provide the specified service "
		validModules = []
		for module in self.moduleInstances:
			if service in self.moduleInstances[module].services:
				validModules.append(self.moduleInstances[module])
		return validModules
	
	def getBestModuleForService(self, service):
		m = self.getmodulesbyservice(service)
		if len(m)>0:
			return m[0]
		return None
	
	def closeAllModules(self):
		" Deport all modules (for shutdown). Modules are unloaded in the opposite order listed in the config. "
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
		if not os.path.exists("%s/data/%s" % (self.botconfig["bot"]["datadir"], moduleName)):
			os.mkdir("%s/data/%s/" % (self.botconfig["bot"]["datadir"], moduleName))
		return "%s/data/%s/" % (self.botconfig["bot"]["datadir"], moduleName)
	
	def getConfigPath(self, moduleName):
		return "%s/config/%s.yml" % (self.botconfig["bot"]["datadir"], moduleName)
	
	" Utility methods "
	@staticmethod
	def decodePrefix(prefix):
		" Returns an object with nick, username, hostname attributes"
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
		return traceback.format_exc()
	
	@staticmethod
	def messageHasCommand(command, message, requireArgs=False):
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
		return self.config["nick"]
	
	
	" Action Methods "
	def act_PONG(self, data):
		self.sendRaw("PONG :%s" % data)
	
	def act_USER(self, username, hostname, realname):
		self.sendRaw("USER %s %s %s :%s" % (username, hostname, self.botconfig["connection"]["server"], realname))
	
	def act_NICK(self, newNick):
		self.sendRaw("NICK %s" % newNick)
	
	def act_JOIN(self, channel):
		self.sendRaw("JOIN %s"%channel)
	
	def act_PRIVMSG(self, towho, message):
		self.sendRaw("PRIVMSG %s :%s"%(towho,message))
	
	def act_MODE(self, channel, mode, extra=None):
		if extra != None:
			self.sendRaw("MODE %s %s %s" % (channel,mode,extra))
		else:
			self.sendRaw("MODE %s %s" % (channel,mode))
	
	def act_ACTION(self, channel, action):
		"""Use the `/me <action>` command
		
		:param channel: The channel name or target's name the message is sent to
		:type channel: str
		:param action: The text to send
		:type action: str
		"""
		self.sendRaw("PRIVMSG %s :\x01ACTION %s"%(channel,action))
	
	def act_KICK(self, channel, who, comment=""):
		"""Use the `/kick <user> <message>` command
		
		:param channel: The channel from which the user will be kicked
		:type channel: str
		:param who: The nickname of the user to kick
		:type action: str
		:param comment: The kick message
		:type comment: str
		"""
		self.sendRaw("KICK %s %s :%s" % (channel, who, comment))
	
