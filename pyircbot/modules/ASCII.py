#!/usr/bin/env python3

"""
.. module::ASCII
    :synopsis: Spam chat with awesome ascii texts
"""

from pyircbot.modulebase import ModuleBase, ModuleHook
from threading import Thread
from glob import iglob
from collections import defaultdict
from time import sleep
import re
import os


RE_ASCII_FNAME = re.compile(r'^[a-zA-Z0-9\-_]+$')


class ASCII(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.hooks.append(ModuleHook("PRIVMSG", self.listen_msg))
        self.running_asciis = defaultdict(lambda: None)
        self.killed_channels = defaultdict(lambda: False)

    def listen_msg(self, msg):
        """
        Handle commands
        :param msg: Message object to inspect
        """
        # Ignore PMs
        if not msg.args[0].startswith("#"):
            return

        # provide a listing of available asciis
        if self.bot.messageHasCommand(".listascii", msg.trailing):
            fnames = [os.path.basename(f).split(".", 2)[0] for f in iglob(os.path.join(self.getFilePath(), "*.txt"))]
            fnames.sort()

            message = "Avalable asciis: {}".format(", ".join(fnames[0:self.config.get("list_max")]))
            self.bot.act_PRIVMSG(msg.args[0], message)

            if len(fnames) > self.config.get("list_max"):
                self.bot.act_PRIVMSG(msg.args[0], "...and {} more".format(len(fnames) - self.config.get("list_max")))
            return

        # Send out an ascii
        cmd = self.bot.messageHasCommand(".ascii", msg.trailing, requireArgs=True)
        if self.bot.messageHasCommand(".ascii", msg.trailing):
            # Prevent parallel spamming in same channel
            if self.running_asciis[msg.args[0]]:
                return

            # Prevent parallel spamming in different channels
            if not self.config.get("allow_parallel") and any(self.running_asciis.values()):
                return

            ascii_name = cmd.args.pop(0)
            if not RE_ASCII_FNAME.match(ascii_name):
                return

            ascii_path = self.getFilePath(ascii_name + ".txt")
            if os.path.exists(ascii_path):
                args = [ascii_path, msg.args[0]]
                if self.config.get("allow_hilight", False) and len(cmd.args) >= 1:
                    args.append(cmd.args.pop(0))
                self.running_asciis[msg.args[0]] = Thread(target=self.print_ascii, args=args, daemon=True)
                self.running_asciis[msg.args[0]].start()
            return

        # stop running asciis
        if self.bot.messageHasCommand(".stopascii", msg.trailing):
            if self.running_asciis[msg.args[0]]:
                self.killed_channels[msg.args[0]] = True

    def print_ascii(self, ascii_path, channel, hilight=None):
        """
        Print the contents of ascii_path to channel
        :param ascii_path: file path to the ascii art file to read and print
        :param channel: channel name to print to
        """
        delay = self.config.get("line_delay")
        with open(ascii_path, "rb") as f:
            content = [i.rstrip() for i in f.read().decode("UTF-8", errors="ignore").split("\n")]
        for line in content:
            if self.killed_channels[channel]:
                break
            if not line:
                line = " "
            if hilight:
                line = "{}: {}".format(hilight, line)
            self.bot.act_PRIVMSG(channel, line)
            if delay:
                sleep(delay)
        del self.running_asciis[channel]
        del self.killed_channels[channel]
