#!/usr/bin/env python
"""
.. module:: GameBase
	:synopsis: A codebase for making IRC games

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
import random
import yaml
import os
import time
from threading import Timer

class GameBase(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.gotMsg)]
		self.loadConfig()
		# Load attribute storage
		self.attr = self.bot.getBestModuleForService("attributes")
		# Load doge RPC
		self.doge = self.bot.getBestModuleForService("dogerpc")
		# Dict of #channel -> game object
		self.games = {}
	
	def gotMsg(self, args, prefix, trailing):
		prefixObj = self.bot.decodePrefix(prefix)
		# Ignore messages from users not logged in
		if self.attr.getKey(prefixObj.nick, "loggedinfrom")==None:
			# Send them a hint?
			return
		else:
			if args[0][0] == "#":
				# create a blank game obj if there isn't one (and whitelisted ? )
				if not args[0] in self.games and (not self.config["channelWhitelistOn"] or (self.config["channelWhitelistOn"] and args[0][1:] in self.config["channelWhitelist"]) ):
					self.games[args[0]]=gameObj(self, args[0])
				# Channel message
				self.games[args[0]].gotMsg(args, prefix, trailing)
			else:
				# Private message
				#self.games[args[0]].gotPrivMsg(args, prefix, trailing)
				pass
	
	def ondisable(self):
		self.log.info("GameBase: Unload requested, ending games...")
		for game in self.games:
			self.games[game].gameover()

class gameObj:
	def __init__(self, master, channel):
		self.master = master
		self.channel = channel
	
	def gotPrivMsg(self, args, prefix, trailing):
		prefix = self.master.bot.decodePrefix(prefix)
		pass
	
	def gotMsg(self, args, prefix, trailing):
		prefix = self.master.bot.decodePrefix(prefix)
		pass
		
		#senderIsOp = self.master.attr.getKey(prefix.nick, "op")=="yes"
	def gameover(self):
		pass

class playerObj:
	def __init__(self, game, nick):
		self.game = game
		self.nick = nick
	
