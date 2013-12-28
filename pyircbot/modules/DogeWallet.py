#!/usr/bin/env python
from modulebase import ModuleBase,ModuleHook
import time
import hashlib

class DogeWallet(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.gotmsg)]
		# Load attribute storage
		self.attr = self.bot.getBestModuleForService("attributes")
		# Load doge RPC
		self.doge = self.bot.getBestModuleForService("dogerpc")
		
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
				oldpass = self.attr.getAttribute(prefix.nick, "password")
				if oldpass == None:
					self.attr.setAttribute(prefix.nick, "password", cmd.args[0])
					self.bot.act_PRIVMSG(prefix.nick, ".setpass: Your password has been set to \"%s\"." % cmd.args[0])
				else:
					if len(cmd.args)==2:
						if cmd.args[0] == oldpass:
							self.attr.setAttribute(prefix.nick, "password", cmd.args[1])
							self.bot.act_PRIVMSG(prefix.nick, ".setpass: Your password has been set to \"%s\"." % cmd.args[1])
						else:
							self.bot.act_PRIVMSG(prefix.nick, ".setpass: Old password incorrect.")
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".setpass: You must provide the old password when setting a new one.")
		cmd = self.bot.messageHasCommand(".setdogeaddr", trailing)
		if cmd:
			userpw = self.attr.getAttribute(prefix.nick, "password")
			if userpw==None:
				self.bot.act_PRIVMSG(prefix.nick, ".setdogeaddr: You must first set a password with .setpass")
			else:
				if len(cmd.args)==2:
					if userpw == cmd.args[0]:
						self.attr.setAttribute(prefix.nick, "dogeaddr", cmd.args[1])
						self.bot.act_PRIVMSG(prefix.nick, ".setdogeaddr: Your doge address has been set to \"%s\"." % cmd.args[1])
						# if they don't have a wallet name, we'll make one now
						if self.attr.getAttribute(prefix.nick, "dogeaccountname")==None:
							randName = self.md5(str(time.time()))[0:10]
							self.attr.setAttribute(prefix.nick, "dogeaccountname", randName)
						
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".setdogeaddr: incorrect password.")
				else:
					self.bot.act_PRIVMSG(prefix.nick, ".setdogeaddr: usage: \".setdogeaddr password address\" or \".setdogeaddr mypassword D8VNy3zkMGspffcFSWWqsxx7GrtVsmF2up\"")
		
		cmd = self.bot.messageHasCommand(".getdogebal", trailing)
		if cmd:
			userpw = self.attr.getAttribute(prefix.nick, "password")
			if userpw==None:
				self.bot.act_PRIVMSG(prefix.nick, ".getdogebal: You must first set a password with .setpass")
			else:
				if len(cmd.args)==1:
					if userpw == cmd.args[0]:
						#################
						walletname = self.attr.getAttribute(prefix.nick, "dogeaccountname")
						amount = 0.0
						if walletname:
							amount = self.doge.getBal(walletname)
						
						self.bot.act_PRIVMSG(prefix.nick, ".getdogebal: Your balance is: %s DOGE" % amount)
						
						#################
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".getdogebal: incorrect password.")
				else:
					self.bot.act_PRIVMSG(prefix.nick, ".getdogebal: usage: \".getdogebal password\"")
		
		cmd = self.bot.messageHasCommand(".withdrawdoge", trailing)
		if cmd:
			userpw = self.attr.getAttribute(prefix.nick, "password")
			useraddr = self.attr.getAttribute(prefix.nick, "dogeaddr")
			if userpw==None:
				self.bot.act_PRIVMSG(prefix.nick, ".withdrawdoge: You must first set a password with .setpass")
			elif useraddr==None:
				self.bot.act_PRIVMSG(prefix.nick, ".withdrawdoge: You must first set a withdraw address .setdogeaddr")
			else:
				if len(cmd.args)==2:
					if userpw == cmd.args[0]:
						#################
						walletname = self.attr.getAttribute(prefix.nick, "dogeaccountname")
						walletbal = self.doge.getBal(walletname)
						
						desiredAmount = float(cmd.args[1])
						
						if walletbal >= desiredAmount:
							txn = self.doge.send(walletname, useraddr, desiredAmount)
							if txn:
								self.bot.act_PRIVMSG(prefix.nick, ".withdrawdoge: %s DOGE sent to %s. Transaction ID: %s"% (desiredAmount, useraddr, txn))
							else:
								self.bot.act_PRIVMSG(prefix.nick, ".withdrawdoge: Unable to create transaction. Please contact an Operator.")
						else:
							self.bot.act_PRIVMSG(prefix.nick, ".withdrawdoge: You only have %s DOGE. You cannot withdraw %s DOGE." % (walletbal, desiredAmount))
						#################
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".withdrawdoge: incorrect password.")
				else:
					self.bot.act_PRIVMSG(prefix.nick, ".withdrawdoge: usage: \".withdrawdoge password amount\" - \".withdrawdoge mypassword 5.0\" - ")
		
		cmd = self.bot.messageHasCommand(".getdepositaddr", trailing)
		if cmd:
			userpw = self.attr.getAttribute(prefix.nick, "password")
			if userpw==None:
				self.bot.act_PRIVMSG(prefix.nick, ".getdepositaddr: You must first set a password with .setpass")
			else:
				if len(cmd.args)==1:
					if userpw == cmd.args[0]:
						#################
						walletname = self.attr.getAttribute(prefix.nick, "dogeaccountname")
						addr = self.doge.getAcctAddr(walletname)
						self.bot.act_PRIVMSG(prefix.nick, ".getdepositaddr: Your deposit address is: %s" % addr)
						#################
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".getdepositaddr: incorrect password.")
				else:
					self.bot.act_PRIVMSG(prefix.nick, ".getdepositaddr: usage: \".getdepositaddr password\"")
		
		
		
		cmd = self.bot.messageHasCommand(".login", trailing)
		if cmd:
			userpw = self.attr.getAttribute(prefix.nick, "password")
			if userpw==None:
				self.bot.act_PRIVMSG(prefix.nick, ".login: You must first set a password with .setpass")
			else:
				if len(cmd.args)==1:
					if userpw == cmd.args[0]:
						#################
						self.attr.setAttribute(prefix.nick, "loggedinfrom", prefix.hostname)
						self.bot.act_PRIVMSG(prefix.nick, ".login: You have been logged in from: %s" % prefix.hostname)
						#################
					else:
						self.bot.act_PRIVMSG(prefix.nick, ".login: incorrect password.")
				else:
					self.bot.act_PRIVMSG(prefix.nick, ".login: usage: \".login password\"")
		cmd = self.bot.messageHasCommand(".logout", trailing)
		if cmd:
			loggedin = self.attr.getAttribute(prefix.nick, "loggedinfrom")
			if loggedin == None:
				self.bot.act_PRIVMSG(prefix.nick, ".logout: You must first be logged in")
			else:
				self.attr.setAttribute(prefix.nick, "loggedinfrom", None)
				self.bot.act_PRIVMSG(prefix.nick, ".logout: You have been logged out.")
	
	def md5(self, data):
		m = hashlib.md5()
		m.update(data.encode("ascii"))
		return m.hexdigest()
