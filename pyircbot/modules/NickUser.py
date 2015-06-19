#!/usr/bin/env python
"""
.. module:: NickUser
	:synopsis: A module providing a simple login/logout account service

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
import time
import hashlib

class NickUser(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.gotmsg)]
		self.services=["login"]
	
	def check(self, nick, hostname):
		attr = self.bot.getBestModuleForService("attributes")
		loggedin = attr.getKey(nick, "loggedinfrom")
		if hostname==loggedin:
			return True
		return False
	
	def ondisable(self):
		pass
		# TODO: log out all users
	
	def gotmsg(self, args, prefix, trailing):
		channel = args[0]
		if channel[0] == "#":
			# Ignore channel messages
			pass
		else:
			self.handlePm(args, prefix, trailing)
	
	def handlePm(self, args, prefix, trailing):
		prefix = self.bot.decodePrefix(prefix)
		cmd = self.bot.messageHasCommand(".setpass", trailing)
		if cmd:
			if len(cmd.args)==0:
				self.bot.act_PRIVMSG(prefix.nick, ".setpass: usage: \".setpass newpass\" or \".setpass oldpass newpass\"")
			else:
				attr = self.bot.getBestModuleForService("attributes")
				oldpass = attr.getKey(prefix.nick, "password")
				if oldpass == None:
					attr.setKey(prefix.nick, "password", cmd.args[0])
					self.bot.act_PRIVMSG(prefix.nick, ".setpass: Your password has been set to \"%s\"." % cmd.args[0])
				else:
					if len(cmd.args)==2:
						if cmd.args[0] == oldpass:
							attr.setKey(prefix.nick, "password", cmd.args[1])
							self.bot.act_PRIVMSG(prefix.nick, ".setpass: Your password has been set to \"%s\"." % cmd.args[1])
						else:
							self.bot.act_PRIVMSG(prefix.nick, ".setpass: Old password incorrect.")
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".setpass: You must provide the old password when setting a new one.")
		
		cmd = self.bot.messageHasCommand(".login", trailing)
		if cmd:
			attr = self.bot.getBestModuleForService("attributes")
			userpw = attr.getKey(prefix.nick, "password")
			if userpw==None:
				self.bot.act_PRIVMSG(prefix.nick, ".login: You must first set a password with .setpass")
			else:
				if len(cmd.args)==1:
					if userpw == cmd.args[0]:
						#################
						attr.setKey(prefix.nick, "loggedinfrom", prefix.hostname)
						self.bot.act_PRIVMSG(prefix.nick, ".login: You have been logged in from: %s" % prefix.hostname)
						#################
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".login: incorrect password.")
				else:
					self.bot.act_PRIVMSG(prefix.nick, ".login: usage: \".login password\"")
		cmd = self.bot.messageHasCommand(".logout", trailing)
		if cmd:
			attr = self.bot.getBestModuleForService("attributes")
			loggedin = attr.getKey(prefix.nick, "loggedinfrom")
			if loggedin == None:
				self.bot.act_PRIVMSG(prefix.nick, ".logout: You must first be logged in")
			else:
				attr.setKey(prefix.nick, "loggedinfrom", None)
				self.bot.act_PRIVMSG(prefix.nick, ".logout: You have been logged out.")
	
	def md5(self, data):
		m = hashlib.md5()
		m.update(data.encode("ascii"))
		return m.hexdigest()
