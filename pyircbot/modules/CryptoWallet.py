#!/usr/bin/env python
"""
.. module:: Error
    :synopsis: Module to provide a multi-type cryptocurrency wallet

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, command
from pyircbot.modules.ModInfo import info
from decimal import Decimal
import time
import hashlib


class CryptoWallet(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)

    def getMods(self):
        return (self.bot.getBestModuleForService("attributes"), self.bot.getBestModuleForService("bitcoinrpc"))

    @info("setaddr <currency> <address>", "set withdraw address", cmds=["setaddr"])
    @command("setaddr", require_args=2, allow_private=True)
    def handle_setaddr(self, msg, cmd):
        if not self.check_login(msg.prefix, msg.args[0]):
            return
        attr, rpc = self.getMods()
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(msg.args[0], ".setaddr: '{}' is not a supported currency. Supported currencies are: {}"
                                 .format(cmd.args[0], supportedStr))
            return
        client = rpc.getRpc(cmd.args[0])
        if not client.validate_addr(cmd.args[1]):
            self.bot.act_PRIVMSG(msg.args[0], ".setaddr: '{}' appears to be an invalid address.".format(cmd.args[1]))
            return

        # Just make sure they have a wallet
        self.checkUserHasWallet(msg.prefix.nick, cmd.args[0])

        # Set their address
        attr.setKey(msg.prefix.nick, "cryptowallet-{}-address".format(cmd.args[0].lower()), cmd.args[1])
        self.bot.act_PRIVMSG(msg.args[0], ".setaddr: Your address has been saved as: {}. Please verify that this is "
                             "correct or your coins could be lost.".format(cmd.args[1]))

    @info("getbal <currency>", "retrieve your balance ", cmds=["getbal"])
    @command("getbal", require_args=1, allow_private=True)
    def handle_getbal(self, msg, cmd):
        if not self.check_login(msg.prefix, msg.args[0]):
            return
        attr, rpc = self.getMods()
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(msg.args[0],
                                 ".getbal: '{}' is not a supported currency. Supported currencies are: {}"
                                 .format(cmd.args[0], supportedStr))
            return

        # Just make sure they have a wallet
        self.checkUserHasWallet(msg.prefix.nick, cmd.args[0])

        # fetch RPC and tell them the balance
        walletname = attr.getKey(msg.prefix.nick, "cryptowallet-account-{}".format(cmd.args[0].lower()))
        amount = 0.0
        if walletname:
            client = rpc.getRpc(cmd.args[0].lower())
            amount = client.getBal(walletname)
            self.bot.act_PRIVMSG(msg.args[0],
                                 "{}: your balance is: {} {}".format(msg.prefix.nick, amount, cmd.args[0].upper()))

    @info("withdraw <currency> <amount>", "send coins to your withdraw address", cmds=["withdraw"])
    @command("withdraw", require_args=2, allow_private=True)
    def handle_withdraw(self, msg, cmd):
        if not self.check_login(msg.prefix, msg.args[0]):
            return
        attr, rpc = self.getMods()
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(msg.args[0], ".getbal: '{}' is not a supported currency. Supported currencies are: {}"
                                 .format(cmd.args[0], supportedStr))
            return

        # Just make sure they have a wallet
        self.checkUserHasWallet(msg.prefix.nick, cmd.args[0])

        # check that they have a withdraw addr
        withdrawaddr = attr.getKey(msg.prefix.nick, "cryptowallet-{}-address".format(cmd.args[0].lower()))
        if withdrawaddr is None:
            self.bot.act_PRIVMSG(msg.args[0], ".withdraw: You need to set a withdraw address before withdrawing. "
                                              "Try .setaddr")
            return

        # fetch RPC and check balance
        walletname = attr.getKey(msg.prefix.nick, "cryptowallet-account-{}".format(cmd.args[0].lower()))
        balance = 0.0

        client = rpc.getRpc(cmd.args[0].lower())
        balance = client.getBal(walletname)
        withdrawamount = Decimal(cmd.args[1])

        if balance < withdrawamount or withdrawamount < 0:
            self.bot.act_PRIVMSG(msg.args[0], ".withdraw: You don't have enough {} to withdraw {}"
                                 .format(cmd.args[0].upper(), withdrawamount))
            return

        if not client.reserve == 0 and balance - client.reserve < withdrawamount:
            self.bot.act_PRIVMSG(msg.args[0], ".withdraw: Withdrawing that much would put you below the reserve "
                                              "({} {}).".format(client.reserve, cmd.args[0].upper()))
            self.bot.act_PRIVMSG(msg.args[0], ".withdraw: The reserve is to cover network transaction fees. To recover "
                                              "it you must close your account. (Talk to my owner)")
            return

        # Check if the precision is wrong
        if not client.checkPrecision(withdrawamount):
            self.bot.act_PRIVMSG(msg.args[0], ".withdraw: {} has maximum {} decimal places"
                                              .format(cmd.args[0].upper(), client.precision))
            return

        # Create a transaction
        txn = client.send(walletname, withdrawaddr, withdrawamount)
        if txn:
            self.bot.act_PRIVMSG(msg.args[0], "{}: .withdraw: {} {} sent to {}."
                                 .format(msg.prefix.nick, withdrawamount, client.name.upper(), withdrawaddr))
            self.bot.act_PRIVMSG(msg.prefix.nick, "Withdrawal: (You)->{}: Transaction ID: {}"
                                 .format(withdrawaddr, txn))
        else:
            self.bot.act_PRIVMSG(msg.args[0], "{}: .withdraw: Transaction create failed. Maybe the transaction was too "
                                              "large for the network? Try a smaller increment.".format(msg.prefix.nick))

    @info("send <currency> <amount> <nick_or_address>", "send coins elsewhere", cmds=["send"])
    @command("send", require_args=3, allow_private=True)
    def handle_send(self, msg, cmd):
        if not self.check_login(msg.prefix, msg.args[0]):
            return
        attr, rpc = self.getMods()
        # Check if currency is known
        curr_name = cmd.args[0].lower()
        if not rpc.isSupported(curr_name):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(msg.args[0], ".getbal: '{}' is not a supported currency. Supported currencies are: {}"
                                 .format(curr_name, supportedStr))
            return

        # Just make sure they have a wallet
        self.checkUserHasWallet(msg.prefix.nick, curr_name)

        # fetch RPC and check balance
        walletname = attr.getKey(msg.prefix.nick, "cryptowallet-account-{}".format(curr_name))
        balance = 0.0

        client = rpc.getRpc(curr_name.lower())
        balance = client.getBal(walletname)
        withdrawamount = Decimal(cmd.args[1])
        tx_dest = cmd.args[2]

        if balance < withdrawamount or withdrawamount < 0:
            self.bot.act_PRIVMSG(msg.args[0], "{}: .send: You don't have enough {} to send {}"
                                              .format(msg.prefix.nick, curr_name.upper(), withdrawamount))
            return

        # Check if the precision is wrong
        if not client.checkPrecision(withdrawamount):
            self.bot.act_PRIVMSG(msg.args[0], ".send: {} has maximum {} decimal places"
                                              .format(curr_name.upper(), client.precision))
            return

        # Check if the tx_dest is a valid address for the coin
        if client.validate_addr(tx_dest):
            # Check if we can cover network fees
            if not client.reserve == 0 and balance - client.reserve < withdrawamount:
                self.bot.act_PRIVMSG(msg.args[0], ".send: Sending that much would put you below the reserve ({} {})."
                                                  .format(client.reserve, curr_name.upper()))
                self.bot.act_PRIVMSG(msg.args[0], ".send: The reserve is to cover network transaction fees. To recover it"
                                                  " you must close your account. (Talk to my owner)")
                return
            # Create a transaction
            txn = client.send(walletname, tx_dest, withdrawamount)
            if txn:
                self.bot.act_PRIVMSG(msg.args[0], "{}: .send: {} {} sent to {}."
                                     .format(msg.prefix.nick, withdrawamount, client.name.upper(), tx_dest))
                self.bot.act_PRIVMSG(msg.prefix.nick, "Send: (You)->{}: Transaction ID: {}".format(tx_dest, txn))
            else:
                self.bot.act_PRIVMSG(msg.args[0], "{}: .send: Transaction create failed. Maybe the address is invalid "
                                                  "or transaction too large for the network?".format(msg.prefix.nick))
        else:
            # Move between local wallets
            # Check if dest user has a password set
            destUserPassword = attr.getKey(tx_dest, "password")
            if destUserPassword is None:
                self.bot.act_PRIVMSG(msg.args[0], "{}: .send: {} doesn't have a password set."
                                                  .format(msg.prefix.nick, tx_dest))
                return

            # Since the user has a password set, check that they have a wallet and create if not
            self.checkUserHasWallet(tx_dest, curr_name)

            srcWalletName = attr.getKey(msg.prefix.nick, "cryptowallet-account-{}".format(curr_name))
            destWalletName = attr.getKey(tx_dest, "cryptowallet-account-{}".format(curr_name))

            assert srcWalletName is not None
            assert destWalletName is not None
            if srcWalletName == destWalletName:
                self.bot.act_PRIVMSG(msg.args[0], "{}: you can't send to yourself!".format(msg.prefix.nick))
                return
            print(srcWalletName)
            print(destWalletName)
            if client.canMove(srcWalletName, destWalletName, withdrawamount):
                if client.move(srcWalletName, destWalletName, withdrawamount):
                    self.bot.act_PRIVMSG(msg.args[0], "{}: .send: {} {} sent to {}."
                                         .format(msg.prefix.nick, withdrawamount, client.name.upper(), tx_dest))
                else:
                    self.bot.act_PRIVMSG(msg.args[0], "{}: uh-oh, something went wrong doing that."
                                                      .format(msg.prefix.nick))

    @info("getaddr <currency>", "get deposit address", cmds=["getaddr"])
    @command("getaddr", require_args=1, allow_private=True)
    def handle_getaddr(self, msg, cmd):
        if not self.check_login(msg.prefix, msg.args[0]):
            return
        attr, rpc = self.getMods()
        # Check if currency is known
        if not rpc.isSupported(cmd.args[0]):
            supportedStr = ', '.join(rpc.getSupported())
            self.bot.act_PRIVMSG(msg.args[0], ".getaddr: '{}' is not a supported currency. Supported currencies are: {}"
                                 .format(cmd.args[0], supportedStr))
            return

        # Just make sure they have a wallet
        self.checkUserHasWallet(msg.prefix.nick, cmd.args[0])

        walletaddr = attr.getKey(msg.prefix.nick, "cryptowallet-depoaddr-{}".format(cmd.args[0].lower()))
        self.bot.act_PRIVMSG(msg.args[0], "{}: your {} deposit address is: {}"
                                          .format(msg.prefix.nick, cmd.args[0].upper(), walletaddr))

    @info("curinfo", "list supported coins", cmds=["curinfo"])
    @command("curinfo", allow_private=True)
    def handle_curinfo(self, msg, cmd):
        attr, rpc = self.getMods()
        if not cmd.args:
            self.bot.act_PRIVMSG(msg.args[0],
                                 ".curinfo: supported currencies: {}. Use '.curinfo BTC' to see details."
                                 .format(', '.join([x.upper() for x in rpc.getSupported()])))
        else:
            if not rpc.isSupported(cmd.args[0]):
                self.bot.act_PRIVMSG(msg.args[0],
                                     ".curinfo: '{}' is not a supported currency. Supported currencies are: {}"
                                     .format(cmd.args[0], ', '.join([x.upper() for x in rpc.getSupported()])))
                return
            else:
                info = rpc.getInfo(cmd.args[0])
                self.bot.act_PRIVMSG(msg.args[0], ".curinfo: {} - {}. More info: {}"
                                     .format(cmd.args[0], info["name"], info["link"]))

    def checkUserHasWallet(self, username, currency):
        # Ensure the user has a wallet in the client
        attr, rpc = self.getMods()
        currency = currency.lower()
        username = username.lower()
        if attr.getKey(username, "cryptowallet-account-{}".format(currency)) is None:
            randName = self.md5(str(time.time()))[0:16]
            attr.setKey(username, "cryptowallet-account-{}".format(currency), randName)
            # Generate a deposit addr to nudge the wallet
            wallet = rpc.getRpc(currency.lower())
            address = wallet.getAcctAddr(randName)
            attr.setKey(username, "cryptowallet-depoaddr-{}".format(currency), address)
        elif attr.getKey(username, "cryptowallet-depoaddr-{}".format(currency)) is None:
            walletName = attr.getKey(username, "cryptowallet-account-{}".format(currency))
            wallet = rpc.getRpc(currency.lower())
            address = wallet.getAcctAddr(walletName)
            attr.setKey(username, "cryptowallet-depoaddr-{}".format(currency), address)

    def check_login(self, prefix, replyTo):
        login = self.bot.getBestModuleForService("login")
        if not login.check(prefix.nick, prefix.hostname):
            self.bot.act_PRIVMSG(replyTo, "{}: Please .login to use this command.".format(prefix.nick))
            return False
        return True

    def md5(self, data):
        m = hashlib.md5()
        m.update(data.encode("ascii"))
        return m.hexdigest()
