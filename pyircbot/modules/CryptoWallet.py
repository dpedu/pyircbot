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
        self.hooks=[ModuleHook("PRIVMSG", self.handle_message)]
    
    def getMods(self):
        return (self.bot.getBestModuleForService("attributes"), self.bot.getBestModuleForService("bitcoinrpc"))
    
    def handle_setaddr(self, args, prefix, trailing, cmd):
        usage = ".setaddr <currency> <address>"
        attr,rpc = self.getMods()
        
        # Check for args
        if not len(cmd.args)==2:
            self.bot.act_PRIVMSG(args[0], ".setaddr: usage: %s" % usage)
            #self.bot.act_PRIVMSG(args[0], ".setaddr: usage: .setaddr BTC 1xyWx6X5EABprhe3s9XduNxLn5NCtpSNB")
            return
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(args[0], ".setaddr: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
            return
        if len(cmd.args[1])<16 or len(cmd.args[1])>42:
            self.bot.act_PRIVMSG(args[0], ".setaddr: '%s' appears to be an invalid address." % (cmd.args[1]))
            return
        
        # Just make sure they have a wallet
        self.checkUserHasWallet(prefix.nick, cmd.args[0])
        
        # Set their address
        attr.setKey(prefix.nick, "cryptowallet-%s-address"%cmd.args[0].lower(), cmd.args[1])
        self.bot.act_PRIVMSG(args[0], ".setaddr: Your address has been saved as: %s. Please verify that this is correct or your coins could be lost." % (cmd.args[1]))
    
    def handle_getbal(self, args, prefix, trailing, cmd):
        usage = ".getbal <currency>"
        attr,rpc = self.getMods()
        # Check for args
        if not len(cmd.args)==1:
            self.bot.act_PRIVMSG(args[0], ".getbal: usage: %s" % usage)
            self.bot.act_PRIVMSG(args[0], ".getbal: usage: .getbal BTC")
            return
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(args[0], ".getbal: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
            return
        
        # Just make sure they have a wallet
        self.checkUserHasWallet(prefix.nick, cmd.args[0])
        
        # fetch RPC and tell them the balance
        walletname = attr.getKey(prefix.nick, "cryptowallet-account-%s"%cmd.args[0].lower())
        amount = 0.0
        if walletname:
            client = rpc.getRpc(cmd.args[0].lower())
            amount = client.getBal(walletname)
            self.bot.act_PRIVMSG(args[0], "%s: your balance is: %s %s" % (prefix.nick, amount, cmd.args[0].upper()))
    
    def handle_withdraw(self, args, prefix, trailing, cmd):
        usage = ".withdraw <currency> <amount>"
        attr,rpc = self.getMods()
        # Check for args
        if not len(cmd.args)==2:
            self.bot.act_PRIVMSG(args[0], ".withdraw: usage: %s" % usage)
            self.bot.act_PRIVMSG(args[0], ".withdraw: usage: .getbal BTC 0.035")
            return
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(args[0], ".getbal: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
            return
        
        # Just make sure they have a wallet
        self.checkUserHasWallet(prefix.nick, cmd.args[0])
        
        # check that they have a withdraw addr
        withdrawaddr = attr.getKey(prefix.nick, "cryptowallet-%s-address"%cmd.args[0].lower())
        if withdrawaddr == None:
            self.bot.act_PRIVMSG(args[0], ".withdraw: You need to set a withdraw address before withdrawing. Try .setaddr")
            return
        
        # fetch RPC and check balance
        walletname = attr.getKey(prefix.nick, "cryptowallet-account-%s"%cmd.args[0].lower())
        balance = 0.0
        
        client = rpc.getRpc(cmd.args[0].lower())
        balance = client.getBal(walletname)
        withdrawamount = float(cmd.args[1])
        
        if balance < withdrawamount or withdrawamount<0:
            self.bot.act_PRIVMSG(args[0], ".withdraw: You don't have enough %s to withdraw %s" % (cmd.args[0].upper(), withdrawamount))
            return
        
        if not client.reserve == 0 and balance - client.reserve < withdrawamount:
            self.bot.act_PRIVMSG(args[0], ".withdraw: Withdrawing that much would put you below the reserve (%s %s)." % (client.reserve, cmd.args[0].upper()))
            self.bot.act_PRIVMSG(args[0], ".withdraw: The reserve is to cover network transaction fees. To recover it you must close your account. (Talk to an admin)")
            return
        
        # Check if the precision is wrong
        if not client.checkPrecision(withdrawamount):
            self.bot.act_PRIVMSG(args[0], ".withdraw: %s has maximum %s decimal places" % (cmd.args[0].upper(), client.precision))
            return
        
        # Create a transaction
        txn = client.send(walletname, withdrawaddr, withdrawamount)
        if txn:
            self.bot.act_PRIVMSG(args[0], "%s: .withdraw: %s %s sent to %s. "% (prefix.nick, withdrawamount, client.name, withdrawaddr))
            self.bot.act_PRIVMSG(prefix.nick, "Withdrawal: (You)->%s: Transaction ID: %s" % (prefix.nick, withdrawaddr, txn))
        else:
            self.bot.act_PRIVMSG(args[0], "%s: .withdraw: Transaction create failed. Maybe the transaction was too large for the network? Try a smaller increment."prefix.nick)
    
    def handle_send(self, args, prefix, trailing, cmd):
        usage = ".send <currency> <amount> <nick or address>"
        attr,rpc = self.getMods()
        # Check for args
        if not len(cmd.args)==3:
            self.bot.act_PRIVMSG(args[0], ".withdraw: usage: %s" % usage)
            self.bot.act_PRIVMSG(args[0], ".withdraw: usage: .getbal BTC 0.035")
            return
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(args[0], ".getbal: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
            return
            
        # Just make sure they have a wallet
        self.checkUserHasWallet(prefix.nick, cmd.args[0])
        
        # fetch RPC and check balance
        walletname = attr.getKey(prefix.nick, "cryptowallet-account-%s"%cmd.args[0].lower())
        balance = 0.0
        
        client = rpc.getRpc(cmd.args[0].lower())
        balance = client.getBal(walletname)
        withdrawamount = float(cmd.args[1])
        
        if balance < withdrawamount or withdrawamount<0:
            self.bot.act_PRIVMSG(args[0], "%s: .send: You don't have enough %s to send %s" % (prefix.nick, cmd.args[0].upper(), withdrawamount))
            return
        
        # Check if the precision is wrong
        if not client.checkPrecision(withdrawamount):
            self.bot.act_PRIVMSG(args[0], ".send: %s has maximum %s decimal places" % (cmd.args[0].upper(), client.precision))
            return
        
        # Check if the recierver is a dogecoin address
        if len(cmd.args[2]) == 34 and cmd.args[2][0:1]=="D":
            # Check if we can cover network fees
            if not client.reserve == 0 and balance - client.reserve < withdrawamount:
                self.bot.act_PRIVMSG(args[0], ".send: Sending that much would put you below the reserve (%s %s)." % (client.reserve, cmd.args[0].upper()))
                self.bot.act_PRIVMSG(args[0], ".send: The reserve is to cover network transaction fees. To recover it you must close your account. (Talk to an admin)")
                return
            
            # Create a transaction
            txn = client.send(walletname, cmd.args[2], withdrawamount)
            if txn:
                self.bot.act_PRIVMSG(args[0], "%s: .send: %s %s sent to %s. "% (prefix.nick, withdrawamount, client.name, cmd.args[2]))
                self.bot.act_PRIVMSG(prefix.nick, "Send: (You)->%s: Transaction ID: %s" % (cmd.args[2], txn))
            else:
                self.bot.act_PRIVMSG(args[0], "%s: .send: Transaction create failed. Maybe the address is invalid or transaction too large for the network? Try a smaller increment."%prefix.nick)
        
        else:
            # Move between local wallets
            # Check if dest user has a password set
            destUserPassword = attr.getKey(cmd.args[2], "password")
            if destUserPassword == None:
                self.bot.act_PRIVMSG(args[0], "%s .send: %s doesn't have a password set." % (prefix.nick, cmd.args[2]))
                return
            
            # Since the user has a password set, check that they have a wallet and create if not
            self.checkUserHasWallet(cmd.args[2], cmd.args[0])
            
            srcWalletName = attr.getKey(prefix.nick, "cryptowallet-account-%s"%cmd.args[0])
            destWalletName = attr.getKey(cmd.args[2], "cryptowallet-account-%s"%cmd.args[0])
            
            assert srcWalletName is not None
            assert destWalletName is not None
            try:
                assert srcWalletName != destWalletName
            except:
                self.bot.act_PRIVMSG(args[0], "%s: you can't send to yourself!" % prefix.nick)
                return
            print(srcWalletName)
            print(destWalletName)
            if client.canMove(srcWalletName, destWalletName, withdrawamount):
                if client.move(srcWalletName, destWalletName, withdrawamount):
                    self.bot.act_PRIVMSG(args[0], "%s .send: %s %s sent to %s. "% (prefix.nick, withdrawamount, client.name, cmd.args[2]))
                else: 
                    self.bot.act_PRIVMSG(args[0], "%s: uh-oh, something went wrong doing that." % prefix.nick)
    
    def handle_getaddr(self, args, prefix, trailing, cmd):
        attr,rpc = self.getMods()
        usage = ".getaddr <currency>"
        # Check for args
        if not len(cmd.args)==1:
            self.bot.act_PRIVMSG(args[0], ".getaddr: usage: %s" % usage)
            self.bot.act_PRIVMSG(args[0], ".getaddr: usage: .getaddr BTC")
            return
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(args[0], ".getaddr: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], supportedStr))
            return
        
        # Just make sure they have a wallet
        self.checkUserHasWallet(prefix.nick, cmd.args[0])
        
        walletaddr = attr.getKey(prefix.nick, "cryptowallet-depoaddr-%s"%cmd.args[0].lower())
        self.bot.act_PRIVMSG(args[0], "%s: your %s deposit address is: %s" % (prefix.nick, cmd.args[0].upper(), walletaddr))
    
    def handle_curinfo(self, args, prefix, trailing, cmd):
        attr,rpc = self.getMods()
        usage = ".curinfo [<currency>]"
        
        # Check for args
        if len(cmd.args)==0:
            self.bot.act_PRIVMSG(args[0], ".curinfo: supported currencies: %s. Use '.curinfo BTC' to see details. " % ', '.join([x.upper() for x in rpc.getSupported()]))
            return
        else:
            if not rpc.isSupported(cmd.args[0]):
                self.bot.act_PRIVMSG(args[0], ".curinfo: '%s' is not a supported currency. Supported currencies are: %s" % (cmd.args[0], ', '.join([x.upper() for x in rpc.getSupported()])))
                return
            else:
                info = rpc.getInfo(cmd.args[0])
                self.bot.act_PRIVMSG(args[0], ".curinfo: %s - %s. More info: %s" % (args[0], info["name"], info["link"]))
    
    def checkUserHasWallet(self, username, currency):
        # Ensure the user has a wallet in the client
        attr,rpc = self.getMods()
        currency = currency.lower()
        username = username.lower()
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
    
    def handle_message(self, args, prefix, trailing):
        prefix = self.bot.decodePrefix(prefix)
        
        # Free commands
        cmd = self.bot.messageHasCommand(".curinfo", trailing)
        if cmd:
            self.handle_curinfo(args, prefix, trailing, cmd)
        
        # Login protected commands
        cmd = self.bot.messageHasCommand(".setaddr", trailing)
        if cmd and self.check_login(prefix, args[0]):
            self.handle_setaddr(args, prefix, trailing, cmd)
        
        cmd = self.bot.messageHasCommand(".getbal", trailing)
        if cmd and self.check_login(prefix, args[0]):
            self.handle_getbal(args, prefix, trailing, cmd)
        
        cmd = self.bot.messageHasCommand(".withdraw", trailing)
        if cmd and self.check_login(prefix, args[0]):
            self.handle_withdraw(args, prefix, trailing, cmd)
        
        cmd = self.bot.messageHasCommand(".getaddr", trailing)
        if cmd and self.check_login(prefix, args[0]):
            self.handle_getaddr(args, prefix, trailing, cmd)
        
        cmd = self.bot.messageHasCommand(".send", trailing)
        if cmd and self.check_login(prefix, args[0]):
            self.handle_send(args, prefix, trailing, cmd)
    
    def check_login(self, prefix, replyTo):
        login = self.bot.getBestModuleForService("login")
        if not login.check(prefix.nick, prefix.hostname):
            self.bot.act_PRIVMSG(replyTo, "%s: Please .login to use this command." % prefix.nick)
            return False
        return True
    
    def md5(self, data):
        m = hashlib.md5()
        m.update(data.encode("ascii"))
        return m.hexdigest()
