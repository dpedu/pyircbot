#!/usr/bin/env python
"""
.. module:: DogeRPC
    :synopsis: Provides a service for interacting with dogecoind.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase,ModuleHook
from bitcoinrpc.authproxy import AuthServiceProxy

class DogeRPC(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName);
        self.hooks=[]
        self.services=["dogerpc"]
        self.loadConfig()
        self.rpc = DogeController(self)
    
    def getBal(self, acct):
        "Get a balance of a local address or an account "
        return self.getAcctBal(acct)
    
    def getAcctAddr(self, acct):
        "Returns the address for an account. creates if necessary "
        self.rpc.ping()
        addrs = self.rpc.con.getaddressesbyaccount(acct)
        if len(addrs)==0:
            return self.rpc.con.getnewaddress(acct)
        return addrs[0]
    
    def getAcctBal(self, acct):
        "Returns an account's balance"
        self.rpc.ping()
        return float(self.rpc.con.getbalance(acct))
    
    def canMove(self, fromAcct, toAcct, amount):
        "True or false if fromAcct can afford to give toAcct an amount of coins "
        balfrom = self.getAcctBal(fromAcct)
        return balfrom >= amount
    
    def move(self, fromAcct, toAcct, amount):
        "Move coins from one account to another "
        self.rpc.ping()
        if self.canMove(fromAcct, toAcct, amount):
            return self.rpc.con.move(fromAcct, toAcct, amount)
        return False
    
    def send(self, fromAcct, toAddr, amount):
        "Send coins to an external addr "
        self.rpc.ping()
        if self.canMove(fromAcct, toAddr, amount):
            return self.rpc.con.sendfrom(fromAcct, toAddr, amount)
        return False

class DogeController:
    "RPC instance control class"
    def __init__(self, master):
        self.config = master.config
        self.log = master.log
        self.con = None
        self.ping()
    
    def ping(self):
        "Test connection and re-establish if necessary"
        if not self.con:
            self.connect()
        try:
            self.con.getinfo()
        except:
            self.connect()
    
    def connect(self):
        "Connect to RPC endpoint"
        self.log.info("DogeRPC: Connecting to dogecoind")
        self.con = AuthServiceProxy("http://%s:%s@%s:%s" % (self.config["username"], self.config["password"], self.config["host"], self.config["port"]))
        self.con.getinfo()
        self.log.info("DogeRPC: Connected to %s:%s" % (self.config["host"], self.config["port"]))
