#!/usr/bin/env python
"""
.. module:: GameBase
    :synopsis: A codebase for making IRC games

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

from pyircbot.modulebase import ModuleBase, ModuleHook
import random
import os
import time
import math
from threading import Timer
from collections import namedtuple


class Election(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks = [ModuleHook("PRIVMSG", self.got_msg), ModuleHook("JOIN", self.join_ch)]
        self.loadConfig()
        self.games = {}

    def got_msg(self, event):
        # Ignore messages from users not logged in
        if event.args[0][0] == "#":
            # Channel message
            self.games[event.args[0]].gotMsg(event)

    def join_ch(self, event):
        print("---------")

        if event.prefix.nick == self.bot.get_nick():
            joined_ch = event.trailing
            if joined_ch not in self.games:
                if self.config["channelWhitelistOn"] and joined_ch not in self.config["channelWhitelist"]:
                    return
                self.games[joined_ch] = ElectionGame(self, joined_ch)

    def ondisable(self):
        self.log.info("GameBase: Unload requested, ending games...")
        for game in self.games:
            self.games[game].gameover()


_game_phases = namedtuple("Phase", "election cooldown halted")
game_phases = _game_phases(0, 1, 2)


class ElectionGame:
    def __init__(self, master, channel):
        self.master = master
        self.bot = master.bot
        self.channel = channel

        self.state = game_phases.election

        self.election_length_s = self.master.config.get('duration', 30)
        self.cooldown_length_s = self.master.config.get('cooldown', 30)
        self.ends_at = time.time() + self.election_length_s

        self.end_timer = None
        self.cooldown_timer = None

        self.start_election()

    def start_election(self):
        self.cooldown_timer = None
        self.votes = dict(**{i: [] for i in self.master.config["choices"]})
        self.state = game_phases.election
        self.end_timer = Timer(self.election_length_s, self.end_election)
        self.end_timer.start()
        self.bot.act_PRIVMSG(self.channel, "[Election started] - vote with '.vote <item>' choosing from: {}."
                                           " Ends in {}".format(', '.join(self.votes.keys()),
                                                                self.format_seconds(self.election_length_s)))

    def end_election(self):
        self.end_timer = None
        self.state = game_phases.cooldown
        self.print_results(prefix="[Election finished] ")

        # Only start a new game if someone voted
        if sum([len(i) for i in self.votes.values()]) > 0:
            self.cooldown_timer = Timer(self.cooldown_length_s, self.start_election)
            self.cooldown_timer.start()
            self.bot.act_PRIVMSG(self.channel, "Next election starts in: {}s".format(self.cooldown_length_s))
        else:
            self.state = game_phases.halted

    def gotMsg(self, event):
        if self.state == game_phases.halted:
            cmd = self.master.bot.messageHasCommand(".election", event.trailing)
            if cmd:
                self.start_election()

        if self.state == game_phases.election:
            cmd = self.master.bot.messageHasCommand(".vote", event.trailing, requireArgs=True)
            if cmd:
                if cmd.args[0] in self.votes.keys():
                    for target in self.votes:
                        try:
                            self.votes[target].remove(event.prefix.nick)
                        except ValueError:
                            pass
                    self.votes[cmd.args[0]].append(event.prefix.nick)
                else:
                    # Invalid candidate
                    pass

            cmd = self.master.bot.messageHasCommand(".votes", event.trailing)

            if cmd:
                self.print_results(show_remaining_time=True)

        else:
            # No election running, pass
            pass

    def print_results(self, prefix='', postfix='', show_remaining_time=False):
        results = ['{} - {}'.format(candidate, len(voters)) for candidate, voters in self.votes.items()]

        togo_info = ""
        if show_remaining_time:
            togo_info = " | ends in {}".format(self.format_seconds(self.ends_at - time.time()))

        self.bot.act_PRIVMSG(self.channel, "{}{}{}{}".format(prefix, ', '.join(results), postfix, togo_info))

    def gameover(self):
        for t in [self.end_timer, self.cooldown_timer]:
            if t:
                t.cancel()

    def format_seconds(self, secs):
        """
        Turns '90' into '1m30s'
        """
        output = ""
        minutes = 0
        if secs > 60:
            minutes = math.floor(secs / 60)
            output += "{}m".format(minutes)
        secs -= minutes * 60

        output += "{}s".format(round(secs))


        return output

