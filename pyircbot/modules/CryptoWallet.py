#!/usr/bin/env python
"""
.. module:: Error
	:synopsis: Module to provide a multi-type cryptocurrency wallet

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
import time
import hashlib

class CryptoWallet(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[ModuleHook("PRIVMSG", self.gotmsg)]
	
	def gotmsg(self, args, prefix, trailing):
		channel = args[0]
		if channel[0] == "#":
			# Ignore channel messages
			pass
		else:
			self.handlePm(args, prefix, trailing)
	
	def getMods(self):
		return (self.bot.getBestModuleForService("attributes"), self.bot.getBestModuleForService("login"), self.bot.getBestModuleForService("bitcoinrpc"))
	
	def handle_setaddr(self, args, prefix, trailing, cmd):
		usage = ".setaddr <currency> <address>"
		attr,login,rpc = self.getMods()
		# Check login
		if not login.check(prefix.nick, prefix.hostname):
			self.bot.act_PRIVMSG(prefix.nick, ".setaddr: Please .login to use this command.")
			return
		# Check for args
		if not len(cmd.args)==2:
			self.bot.act_PRIVMSG(prefix.nick, ".setaddr: usage: %s" % usage)
			self.bot.act_PRIVMSG(prefix.nick, ".setaddr: usage: .setaddr BTC 1xyWx6X5EABprhe3s9XduNxLn5NCtpSNB")
			return
		# Check if currency is known
		if not rpc.isSupported(cmd.args[0]):
			supportedStr = ', '.join(rpc.getSupported())
			self.bot.act_PRIVMSG(prefix.nick, ".setaddr: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
			return
		if len(cmd.args[1])<16 or len(cmd.args[1])>42:
			self.bot.act_PRIVMSG(prefix.nick, ".setaddr: '%s' appears to be an invalid address." % (cmd.args[1]))
			return
		
		# Just make sure they have a wallet
		self.checkUserHasWallet(prefix.nick, cmd.args[0])
		
		# Set their address
		attr.setKey(prefix.nick, "cryptowallet-%s-address"%cmd.args[0].lower(), cmd.args[1])
		self.bot.act_PRIVMSG(prefix.nick, ".setaddr: Your address has been saved as: %s. Please verify that this is correct or your coins could be lost." % (cmd.args[1]))
	
	def handle_getbal(self, args, prefix, trailing, cmd):
		usage = ".getbal <currency>"
		attr,login,rpc = self.getMods()
		# Check login
		if not login.check(prefix.nick, prefix.hostname):
			self.bot.act_PRIVMSG(prefix.nick, ".getbal: Please .login to use this command.")
			return
		# Check for args
		if not len(cmd.args)==1:
			self.bot.act_PRIVMSG(prefix.nick, ".getbal: usage: %s" % usage)
			self.bot.act_PRIVMSG(prefix.nick, ".getbal: usage: .getbal BTC")
			return
		# Check if currency is known
		if not rpc.isSupported(cmd.args[0]):
			supportedStr = ', '.join(rpc.getSupported())
			self.bot.act_PRIVMSG(prefix.nick, ".getbal: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
			return
		
		# Just make sure they have a wallet
		self.checkUserHasWallet(prefix.nick, cmd.args[0])
		
		# fetch RPC and tell them the balance
		walletname = attr.getKey(prefix.nick, "cryptowallet-account-%s"%cmd.args[0].lower())
		amount = 0.0
		if walletname:
			client = rpc.getRpc(cmd.args[0].lower())
			amount = client.getBal(walletname)
			self.bot.act_PRIVMSG(prefix.nick, "Your balance is: %s %s" % (amount, cmd.args[0].upper()))
	
	def handle_withdraw(self, args, prefix, trailing, cmd):
		usage = ".withdraw <currency> <amount>"
		attr,login,rpc = self.getMods()
		# Check login
		if not login.check(prefix.nick, prefix.hostname):
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: Please .login to use this command.")
			return
		# Check for args
		if not len(cmd.args)==2:
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: usage: %s" % usage)
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: usage: .getbal BTC 0.035")
			return
		# Check if currency is known
		if not rpc.isSupported(cmd.args[0]):
			supportedStr = ', '.join(rpc.getSupported())
			self.bot.act_PRIVMSG(prefix.nick, ".getbal: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
			return
		
		# Just make sure they have a wallet
		self.checkUserHasWallet(prefix.nick, cmd.args[0])
		
		# check that they have a withdraw addr
		withdrawaddr = attr.getKey(prefix.nick, "cryptowallet-%s-address"%cmd.args[0].lower())
		if withdrawaddr == None:
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: You need to set a withdraw address before withdrawing. Try .setaddr")
			return
		
		# fetch RPC and check balance
		walletname = attr.getKey(prefix.nick, "cryptowallet-account-%s"%cmd.args[0].lower())
		balance = 0.0
		
		client = rpc.getRpc(cmd.args[0].lower())
		balance = client.getBal(walletname)
		withdrawamount = float(cmd.args[1])
		
		if balance < withdrawamount or withdrawamount<0:
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: You don't have enough %s to withdraw %s" % (cmd.args[0].upper(), withdrawamount))
			return
		
		if not client.reserve == 0 and balance - client.reserve < withdrawamount:
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: Withdrawing that much would put you below the reserve (%s %s)." % (client.reserve, cmd.args[0].upper()))
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: The reserve is to cover network transaction fees. To recover it you must close your account. (Talk to an admin)")
			return
		
		# Check if the precision is wrong
		if not client.checkPrecision(withdrawamount):
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: %s has maximum %s decimal places" % (cmd.args[0].upper(), client.precision))
			return
		
		# Create a transaction
		txn = client.send(walletname, withdrawaddr, withdrawamount)
		if txn:
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: %s %s sent to %s. Transaction ID: %s"% (withdrawamount, client.name, withdrawaddr, txn))
		else:
			self.bot.act_PRIVMSG(prefix.nick, ".withdraw: Transaction create failed. Maybe the transaction was too large for the network? Try a smaller increment.")
	
	def handle_getaddr(self, args, prefix, trailing, cmd):
		attr,login,rpc = self.getMods()
		usage = ".getaddr <currency>"
		attr,login,rpc = self.getMods()
		# Check login
		if not login.check(prefix.nick, prefix.hostname):
			self.bot.act_PRIVMSG(prefix.nick, ".getaddr: Please .login to use this command.")
			return
		# Check for args
		if not len(cmd.args)==1:
			self.bot.act_PRIVMSG(prefix.nick, ".getaddr: usage: %s" % usage)
			self.bot.act_PRIVMSG(prefix.nick, ".getaddr: usage: .getaddr BTC")
			return
		# Check if currency is known
		if not rpc.isSupported(cmd.args[0]):
			supportedStr = ', '.join(rpc.getSupported())
			self.bot.act_PRIVMSG(prefix.nick, ".getaddr: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
			return
		
		# Just make sure they have a wallet
		self.checkUserHasWallet(prefix.nick, cmd.args[0])
		
		walletaddr = attr.getKey(prefix.nick, "cryptowallet-depoaddr-%s"%cmd.args[0].lower())
		self.bot.act_PRIVMSG(prefix.nick, "Your %s deposit address is: %s" % (cmd.args[0].upper(), walletaddr))
	
	def handle_curinfo(self, args, prefix, trailing, cmd):
		attr,login,rpc = self.getMods()
		usage = ".curinfo [<currency>]"
		attr,login,rpc = self.getMods()
		
		# Check for args
		if len(cmd.args)==0:
			self.bot.act_PRIVMSG(prefix.nick, ".curinfo: supported currencies: %s. Use '.curinfo BTC' to see details. " % ', '.join([x.upper() for x in rpc.getSupported()]))
			return
		else:
			if not rpc.isSupported(cmd.args[0]):
				self.bot.act_PRIVMSG(prefix.nick, ".curinfo: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], ', '.join([x.upper() for x in rpc.getSupported()])))
				return
			else:
				info = rpc.getInfo(cmd.args[0])
				self.bot.act_PRIVMSG(prefix.nick, ".curinfo: %s - %s. More info: %s" % (args[0], info["name"], info["link"]))
	
	def checkUserHasWallet(self, username, currency):
		# Ensure the user has a wallet in the client
		attr,login,rpc = self.getMods()
		currency = currency.lower()
		if attr.getKey(username, "cryptowallet-account-%s"%currency)==None:
			randName = self.md5(str(time.time()))[0:16]
			attr.setKey(username, "cryptowallet-account-%s"%currency, randName)
			# Generate a deposit addr to nudge the wallet
			wallet = rpc.getRpc(currency.lower())
			address = wallet.getAcctAddr(randName)
			attr.setKey(username, "cryptowallet-depoaddr-%s"%currency, address)
		elif attr.getKey(username, "cryptowallet-depoaddr-%s"%currency)==None:
			walletName = attr.getKey(username, "cryptowallet-account-%s"%currency)
			wallet = rpc.getRpc(currency.lower())
			address = wallet.getAcctAddr(walletName)
			attr.setKey(username, "cryptowallet-depoaddr-%s"%currency, address)
		
	
	def handlePm(self, args, prefix, trailing):
		prefix = self.bot.decodePrefix(prefix)
		
		cmd = self.bot.messageHasCommand(".setaddr", trailing)
		if cmd:
			self.handle_setaddr(args, prefix, trailing, cmd)
		cmd = self.bot.messageHasCommand(".getbal", trailing)
		if cmd:
			self.handle_getbal(args, prefix, trailing, cmd)
		cmd = self.bot.messageHasCommand(".withdraw", trailing)
		if cmd:
			self.handle_withdraw(args, prefix, trailing, cmd)
		cmd = self.bot.messageHasCommand(".getaddr", trailing)
		if cmd:
			self.handle_getaddr(args, prefix, trailing, cmd)
		cmd = self.bot.messageHasCommand(".curinfo", trailing)
		if cmd:
			self.handle_curinfo(args, prefix, trailing, cmd)
		
	def md5(self, data):
		m = hashlib.md5()
		m.update(data.encode("ascii"))
		return m.hexdigest()
