#!/usr/bin/env python
"""
.. module:: Services
    :synopsis: Provides the ability to configure a nickname, password, channel auto-join

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, hook
from time import sleep


class Services(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.current_preferred_nick = 0
        self.current_nick = None
        self.current_channels = []
        self.do_ghost = False
        self.services = ["services"]

    @hook("_CONNECT")
    def _doConnect(self, msg, cmd):
        """Hook for when the IRC conneciton is opened"""
        self.current_preferred_nick = 0
        self.bot.act_NICK(self.config["user"]["nick"][self.current_preferred_nick])
        self.bot.act_USER(self.config["user"]["username"], self.config["user"]["hostname"],
                          self.config["user"]["realname"])

    @hook("433")
    def _nickTaken(self, msg, cmd):
        """Hook that responds to 433, meaning our nick is taken"""
        if self.config["ident"]["ghost"]:
            self.do_ghost = True
        self.current_preferred_nick += 1
        if self.current_preferred_nick >= len(self.config["user"]["nick"]):
            self.log.critical("Ran out of usernames while selecting backup username!")
            return
        self.bot.act_NICK(self.config["user"]["nick"][self.current_preferred_nick])

    @hook("001")
    def _initservices(self, msg, cmd):
        """Hook that sets our initial nickname"""
        if self.do_ghost:
            self.bot.act_PRIVMSG(self.config["ident"]["ghost_to"], self.config["ident"]["ghost_cmd"] %
                                 {"nick": self.config["user"]["nick"][0], "password": self.config["user"]["password"]})
            sleep(2)
            self.bot.act_NICK(self.config["user"]["nick"][self.current_preferred_nick])
        self.current_nick = self.config["user"]["nick"][self.current_preferred_nick]
        self._do_initservices()

    @hook("INVITE")
    def _invited(self, msg, cmd):
        """Hook responding to INVITE channel invitations"""
        if msg.trailing.lower() in self.config["privatechannels"]["list"]:
            self.log.info("Invited to %s, joining" % msg.trailing)
            self.bot.act_JOIN(msg.trailing)

    def _do_initservices(self):
        """Identify with nickserv and join startup channels"""
        " id to nickserv "
        if self.config["ident"]["enable"]:
            self.bot.act_PRIVMSG(self.config["ident"]["to"], self.config["ident"]["command"] %
                                 {"password": self.config["user"]["password"]})

        " join plain channels "
        for channel in self.config["channels"]:
            self.log.info("Joining %s" % channel)
            self.bot.act_JOIN(channel)

        " request invite for private message channels "
        for channel in self.config["privatechannels"]["list"]:
            self.log.info("Requesting invite to %s" % channel)
            self.bot.act_PRIVMSG(self.config["privatechannels"]["to"], self.config["privatechannels"]["command"] %
                                 {"channel": channel})

    @hook("NICK")
    def _changed_nick(self, msg, cmd):
        if msg.prefix.nick == self.current_nick:
            self.current_nick = msg.trailing

    @hook("JOIN", "PART")
    def _joinpart(self, msg, cmd):
        (self.current_channels.append if msg.command == "JOIN" else self.current_channels.remove)(msg.args[0])

    def nick(self):
        return self.current_nick

    def channels(self):
        return self.current_channels

