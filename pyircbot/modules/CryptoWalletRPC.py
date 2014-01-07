#!/usr/bin/env python
from modulebase import ModuleBase,ModuleHook
from bitcoinrpc.authproxy import AuthServiceProxy
from math import floor
from threading import Thread
from time import sleep

class CryptoWalletRPC(ModuleBase):
	def __init__(self, bot, moduleName):
		ModuleBase.__init__(self, bot, moduleName);
		self.hooks=[]
		self.services=["bitcoinrpc"]
		self.loadConfig()
		self.rpcservices={}
		
		self.loadrpcservices()
	
	def loadrpcservices(self):
		# Create a dict of abbreviation=>BitcoinRPC objcet relation
		self.log.info("CryptoWalletRPC: loadrpcservices: connecting to RPCs")
		count = len(list(self.config["types"].keys()))
		num = 0
		for key in self.config["types"]:
			self.rpcservices[key.lower()]=BitcoinRPC(self, key, self.config["types"][key]["host"], self.config["types"][key]["port"], self.config["types"][key]["username"], self.config["types"][key]["password"], self.config["types"][key]["precision"], self.config["types"][key]["reserve"])
			num+=1
	
	def getRpc(self, currencyAbbr):
		# Return the rpc for the currency requested
		# self.getRpc("LTC") -> returns a litecoin rpc instance
		currencyAbbr = currencyAbbr.lower()
		if currencyAbbr in self.rpcservices:
			return self.rpcservices[currencyAbbr]
		return None
	
	def getSupported(self):
		# return a list of (appreviatons of) supported currencies
		return list(self.rpcservices.keys())
	
	def isSupported(self, abbr):
		# true/false if currency is supported
		supported = self.getSupported()
		return abbr.lower() in supported
	
	def getInfo(self, abbr):
		# return the coin's info from config
		if self.isSupported(abbr):
			return self.config["types"][abbr.upper()]
	

class BitcoinRPC:
	def __init__(self, parent, name, host, port, username, password, precision, reserve):
		# Store info and connect
		self.master = parent
		self.name = name
		self.host = host
		self.port = port
		self.username = username
		self.password = password
		self.precision = precision
		self.reserve = reserve
		self.log = self.master.log
		
		# AuthServiceProxy (json client) stored here
		self.con = None
		# Connect
		Thread(target=self.ping).start()
	
	def getBal(self, acct):
		# get a balance of an address or an account 
		return self.getAcctBal(acct)
	
	def getAcctAddr(self, acct):
		# returns the address for an account. creates if necessary 
		self.ping()
		addrs = self.con.getaddressesbyaccount(acct)
		if len(addrs)==0:
			return self.con.getnewaddress(acct)
		return addrs[0]
	
	def getAcctBal(self, acct):
		# returns an account's balance
		self.ping()
		return float(self.con.getbalance(acct))
	
	def canMove(self, fromAcct, toAcct, amount):
		# true or false if fromAcct can afford to give toAcct an amount of coins 
		balfrom = self.getAcctBal(fromAcct)
		return balfrom >= amount
	
	def move(self, fromAcct, toAcct, amount):
		# move coins from one account to another 
		self.ping()
		if self.canMove(fromAcct, toAcct, amount):
			return self.con.move(fromAcct, toAcct, amount)
		return False
	
	def send(self, fromAcct, toAddr, amount):
		# send coins to an external addr 
		self.ping()
		if self.canMove(fromAcct, toAddr, amount):
			return self.con.sendfrom(fromAcct, toAddr, amount)
		return False
	
	def checkPrecision(self, amount):
		return amount == round(amount, self.precision)
	
	def ping(self):
		# internal. test connection and connect if necessary
		try:
			self.con.getinfo()
		except:
			self.connect()
	
	def connect(self):
		# internal. connect to the service
		self.log.debug("CryptoWalletRPC: %s: Connecting to %s:%s" % (self.name, self.host,self.port))
		try:
			self.con = AuthServiceProxy("http://%s:%s@%s:%s" % (self.username, self.password, self.host, self.port))
		except Exception as e:
			self.log.debug("CryptoWalletRPC: %s: Could not connect to %s:%s: %s" % (self.name, self.host, self.port, str(e)))
			return
		
		self.log.debug("CryptoWalletRPC: %s: Connected to %s:%s" % (self.name, self.host, self.port))
	

