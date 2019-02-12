#!/usr/bin/env python
"""
.. module:: NickUser
    :synopsis: A module providing a simple login/logout account service

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, hook
from pyircbot.common import messageHasCommand
from pyircbot.modules.ModInfo import info


class NickUser(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.services = ["login"]

    def check(self, nick, hostname):
        attr = self.bot.getBestModuleForService("attributes")
        loggedin = attr.getKey(nick, "loggedinfrom")
        if hostname == loggedin:
            return True
        return False

    def ondisable(self):
        pass
        # TODO: log out all users

    @hook("PRIVMSG")
    def gotmsg(self, msg, cmd):
        if msg.args[0][0] == "#":
            # Ignore channel messages
            return
        else:
            self.handlePm(msg.prefix, msg.trailing)

    @info("setpass [<oldpass>] <password>", "set or change password", cmds=["setpass"])
    @info("login <password>", "authenticate with the bot", cmds=["login"])
    @info("logout", "log out of the bot", cmds=["logout"])
    def handlePm(self, prefix, trailing):
        cmd = messageHasCommand(".setpass", trailing)
        if cmd:
            if len(cmd.args) == 0:
                self.bot.act_PRIVMSG(prefix.nick, ".setpass: usage: \".setpass newpass\" or "
                                                  "\".setpass oldpass newpass\"")
            else:
                attr = self.bot.getBestModuleForService("attributes")
                oldpass = attr.getKey(prefix.nick, "password")
                if oldpass is None:
                    attr.setKey(prefix.nick, "password", cmd.args[0])
                    attr.setKey(prefix.nick, "loggedinfrom", prefix.hostname)
                    self.bot.act_PRIVMSG(prefix.nick, ".setpass: You've been logged in and "
                                                      "your password has been set to \"%s\"." % cmd.args[0])
                else:
                    if len(cmd.args) == 2:
                        if cmd.args[0] == oldpass:
                            attr.setKey(prefix.nick, "password", cmd.args[1])
                            self.bot.act_PRIVMSG(prefix.nick,
                                                 ".setpass: Your password has been set to \"%s\"." % cmd.args[1])
                            attr.setKey(prefix.nick, "loggedinfrom", prefix.hostname)
                        else:
                            self.bot.act_PRIVMSG(prefix.nick, ".setpass: Old password incorrect.")
                    else:
                        self.bot.act_PRIVMSG(prefix.nick,
                                             ".setpass: You must provide the old password when setting a new one.")

        cmd = messageHasCommand(".login", trailing)
        if cmd:
            attr = self.bot.getBestModuleForService("attributes")
            userpw = attr.getKey(prefix.nick, "password")
            if userpw is None:
                self.bot.act_PRIVMSG(prefix.nick, ".login: You must first set a password with .setpass")
            else:
                if len(cmd.args) == 1:
                    if userpw == cmd.args[0]:
                        attr.setKey(prefix.nick, "loggedinfrom", prefix.hostname)
                        self.bot.act_PRIVMSG(prefix.nick, ".login: You have been logged in from: %s" % prefix.hostname)
                    else:
                        self.bot.act_PRIVMSG(prefix.nick, ".login: incorrect password.")
                else:
                    self.bot.act_PRIVMSG(prefix.nick, ".login: usage: \".login password\"")
        cmd = messageHasCommand(".logout", trailing)
        if cmd:
            attr = self.bot.getBestModuleForService("attributes")
            loggedin = attr.getKey(prefix.nick, "loggedinfrom")
            if loggedin is None:
                self.bot.act_PRIVMSG(prefix.nick, ".logout: You must first be logged in")
            else:
                attr.setKey(prefix.nick, "loggedinfrom", None)
                self.bot.act_PRIVMSG(prefix.nick, ".logout: You have been logged out.")


# Decorator for methods that require login
# Assumes your args matches the same format that @command(...) expects
class protected(object):
    def __init__(self, message=None):
        self.message = message or "{}: you need to .login to do that"

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            module, message, command = args
            login = module.bot.getBestModuleForService("login")

            if not login.check(message.prefix.nick, message.prefix.hostname):
                module.bot.act_PRIVMSG(message.args[0] if message.args[0].startswith("#") else message.prefix.nick,
                                       self.message.format(message.prefix.nick))
                return

            func(*args, **kwargs)
        return wrapper
