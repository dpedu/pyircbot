#!/usr/bin/env python
"""
.. module:: CryptoWalletRPC
    :synopsis: Module capable of operating bitcoind-style RPC. Provided as a service.

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase
from bitcoinrpc.authproxy import AuthServiceProxy
import re
from threading import Thread
from decimal import Decimal


class CryptoWalletRPC(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.services = ["bitcoinrpc"]
        self.rpcservices = {}
        self.loadrpcservices()

    def loadrpcservices(self):
        # Create a dict of abbreviation=>BitcoinRPC objcet relation
        self.log.info("CryptoWalletRPC: loadrpcservices: connecting to RPCs")
        for abbr, coin in self.config["types"].items():
            self.rpcservices[abbr.lower()] = BitcoinRPC(self.log,
                                                        abbr.lower(),
                                                        coin["name"],
                                                        coin["host"],
                                                        coin["port"],
                                                        coin["username"],
                                                        coin["password"],
                                                        coin["precision"],
                                                        Decimal(coin["reserve"]),
                                                        re.compile(coin["addrfmt"]))

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

    # def validate_addr(self, coin_abbr, address):
    #     client = self.getRpc(coin_abbr.lower())
    #     if not client or not client.validate_addr(:
    #         return False

    def getInfo(self, abbr):
        # return the coin's info from config
        if self.isSupported(abbr):
            return self.config["types"][abbr.upper()]


class BitcoinRPC(object):
    def __init__(self, logger, name, fullname, host, port, username, password, precision, reserve, addr_re):
        # Store info and connect
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.precision = precision
        self.reserve = reserve
        self.addr_re = addr_re
        self.log = logger
        self.con = None  # AuthServiceProxy (bitcoin json rpc client) stored here
        Thread(target=self.ping).start()  # Initiate rpc connection

    def validate_addr(self, addr):
        """
        Validate an address string. Returns true if the `addr` provided is a valid address string
        :param addr: address to validate
        :type addr: str
        :return: bool
        """
        return True if type(addr) is str and self.addr_re.match(addr) else False

    def getBal(self, acct):
        """
        Return the balance of the passed account
        :param acct: account name
        :type acct: str
        :return: decimal.Decimal
        """
        return self.getAcctBal(acct)

    def getAcctAddr(self, acct):
        """
        Return the deposit address associated with the passed account
        :param acct: account name
        :type acct: str
        """
        self.ping()
        addrs = self.con.getaddressesbyaccount(acct)
        if len(addrs) == 0:
            return self.con.getnewaddress(acct)
        return addrs[0]

    def getAcctBal(self, acct):
        # returns an account's balance
        self.ping()
        return Decimal(self.con.getbalance(acct))

    def canMove(self, fromAcct, toAcct, amount):
        # true or false if fromAcct can afford to give toAcct an amount of coins
        balfrom = self.getAcctBal(fromAcct)
        return (balfrom - self.reserve) >= amount

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
        self.log.info("CryptoWalletRPC: %s: Connecting to %s:%s" % (self.name, self.host, self.port))
        try:
            self.con = AuthServiceProxy("http://%s:%s@%s:%s" % (self.username, self.password, self.host, self.port))
        except Exception as e:
            self.log.error("CryptoWalletRPC: %s: Could not connect to %s:%s: %s" %
                           (self.name, self.host, self.port, str(e)))
            return

        self.log.info("CryptoWalletRPC: %s: Connected to %s:%s" % (self.name, self.host, self.port))
