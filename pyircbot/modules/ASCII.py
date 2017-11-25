#!/usr/bin/env python3

"""
.. module::ASCII
    :synopsis: Spam chat with awesome ascii texts
"""

from pyircbot.modulebase import ModuleBase, command
from threading import Thread
from glob import iglob
from collections import defaultdict
from time import sleep
import re
import os
import json
from textwrap import wrap
from pyircbot.modules.ModInfo import info


RE_ASCII_FNAME = re.compile(r'^[a-zA-Z0-9\-_]+$')
IRC_COLOR = "\x03"


def is_numeric(char):
    i = ord(char)
    return i >= 48 and i <= 57


class ASCII(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.running_asciis = defaultdict(lambda: None)
        self.killed_channels = defaultdict(lambda: False)

    @info("listascii         list available asciis", cmds=["listascii"])
    @command("listascii")
    def cmd_listascii(self, msg, cmd):
        """
        List available asciis
        """
        fnames = [os.path.basename(f).split(".", 2)[0] for f in iglob(os.path.join(self.getFilePath(), "*.txt"))]
        fnames.sort()

        message = "Avalable asciis: {}".format(", ".join(fnames[0:self.config.get("list_max")]))
        self.bot.act_PRIVMSG(msg.args[0], message)

        if len(fnames) > self.config.get("list_max"):
            self.bot.act_PRIVMSG(msg.args[0], "...and {} more".format(len(fnames) - self.config.get("list_max")))
        return

    @info("ascii <name>      print an ascii", cmds=["ascii"])
    @command("ascii", require_args=True)
    def cmd_ascii(self, msg, cmd):
        if self.channel_busy(msg.args[0]):
            return

        # Prevent parallel spamming in different channels
        if not self.config.get("allow_parallel") and any(self.running_asciis.values()):
            return

        ascii_name = cmd.args.pop(0)
        if not RE_ASCII_FNAME.match(ascii_name):
            return

        hilight = cmd.args[0] + ": " if self.config.get("allow_hilight", False) and len(cmd.args) >= 1 else False
        try:
            self.send_to_channel(msg.args[0], self.load_ascii(ascii_name), prefix=hilight)
        except FileNotFoundError:
            return

    @info("stopascii         stop the currently scrolling ascii", cmds=["stopascii"])
    @command("stopascii")
    def cmd_stopascii(self, msg, cmd):
        """
        Command to stop the running ascii in a given channel
        """
        if self.running_asciis[msg.args[0]]:
            self.killed_channels[msg.args[0]] = True

    def channel_busy(self, channel_name):
        """
        Prevent parallel spamming in same channel
        """
        if self.running_asciis[channel_name]:
            return True
        return False

    def send_to_channel(self, channel, lines, **kwargs):
        self.running_asciis[channel] = Thread(target=self.print_lines, daemon=True,
                                              args=[channel, lines], kwargs=kwargs)
        self.running_asciis[channel].start()

    def load_ascii(self, ascii_name):
        """
        Loads contents of ascii from disk by name
        :return: list of string lines
        """
        with open(self.getFilePath(ascii_name + ".txt"), "rb") as f:
            return [i.rstrip() for i in f.read().decode("UTF-8", errors="ignore").split("\n")]

    def print_lines(self, channel, lines, prefix=None):
        """
        Print the contents of ascii_path to channel
        :param ascii_path: file path to the ascii art file to read and print
        :param channel: channel name to print to
        """
        delay = self.config.get("line_delay")

        for line in lines:
            if self.killed_channels[channel]:
                break
            if not line:
                line = " "
            if prefix:
                line = "{}{}".format(prefix, line)
            self.bot.act_PRIVMSG(channel, line)
            if delay:
                sleep(delay)
        del self.running_asciis[channel]
        del self.killed_channels[channel]

    @info("asciiedit <args>            customize an ascii with input", cmds=["asciiedit"])
    @command("asciiedit", require_args=True)
    def cmd_asciiedit(self, msg, cmd):
        ascii_name = cmd.args.pop(0)
        try:
            with open(self.getFilePath(ascii_name + ".json")) as f:
                ascii_infos = json.load(f)
            ascii_lines = self.load_ascii(ascii_name)
        except FileNotFoundError:
            return

        template_data = " ".join(cmd.args).split("|")

        for i in range(0, min(len(ascii_infos["areas"]), len(template_data))):
            ascii_infos["areas"][i]["string"] = template_data[i]

        lines = self.edit_ascii(ascii_lines, ascii_infos)
        self.send_to_channel(msg.args[0], lines)

    def edit_ascii(self, lines, info_dict):
        asci = AsciiEdit(lines)
        # Per region in the metadata
        for area in info_dict["areas"]:
            message = area.get("format", "{}").format(area["string"])
            x = area["x"]
            y = area["y"]
            # Format the text to the area's width
            boxed_lines = wrap(message, area["width"])
            # Write each line
            for line in boxed_lines:
                line_x = x
                props = area.get("props", [])
                # move the X over for centered text
                if "centered" in props:
                    padding = (area["width"] - len(line)) / 2
                    line_x += padding
                if "upper" in props:
                    line = line.upper()
                if "lower" in props:
                    line = line.lower()
                if "blacktext" in props:
                    asci.set_charcolor(1)
                # Ensure anything in the template will be covered
                # line = line + " " * (area["width"] - len(line))
                # Write the formatted line
                asci.goto(line_x, y)
                asci.write(line)
                # Check if height limit is passed
                y += 1
                if y >= area["y"] + area["height"]:
                    break
        return asci.getlines()


class AsciiEdit(object):
    """
    Semi-smart ascii editing library
    """
    def __init__(self, lines):
        self.lines = [list(line) for line in lines]
        self.x = 0
        self.virtual_x = 0
        self.y = 0
        self.charcolor = None

    def goto(self, x, y):
        """
        This method moves the internal pointer to the passed X and Y coordinate. The origin is the top left corner.
        The literal coordinates (self.x and self.y) point to where in the data the pointer is. Y is simple, self.y is
        always the data and rendered Y coordinate. X has invisible-when-rendered formatting data, so the self.virtual_x
        attribute tracks where the cursor is in the rendered output; self.x tracks the location in the actual data.
        :param x: x coordinate
        :type x: int
        :param y: y coordinate
        :type y: int
        """
        # Immediately set the x and y pointers
        self.virtual_x = x
        self.y = y
        # Calculate the x position in-data by increasing self.x to the right until real_x == target x
        self.x = 0
        real_x = 0
        while real_x <= x:
            # Scan throw any repeated color codes
            while self.lines[self.y][self.x] == IRC_COLOR:
                # Scan forward until color code is crossed
                self.x += 1  # the escape char
                if is_numeric(self._getchar()):
                    self.x += 1  # color code 1st digit
                    if is_numeric(self._getchar()):
                        self.x += 1  # color code 2nd digit
                # Check for background color code after comma
                if self._getchar() == "," and is_numeric(self._getchar(self.x + 1)):
                    self.x += 2  # comma and background code digit 1
                    if is_numeric(self._getchar()):
                        self.x += 1  # color code digit 2
            real_x += 1
            if real_x <= x:
                self.x += 1

    def set_charcolor(self, color):
        self.charcolor = color

    def write(self, text):
        """
        Write a single line of text to the ascii
        """
        for char in text:
            self._putchar(self.x, self.y, char)
            self.goto(self.virtual_x + 1, self.y)

    def getlines(self):
        """
        Return the rendered ascii, formatted as a list of string lines
        """
        return [''.join(line) for line in self.lines]

    def _getchar(self, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        return self.lines[y][x]

    def _putchar(self, x, y, char):
        if self.charcolor is not None and char != " ":
            self.lines[y].pop(x)
            for char in list((IRC_COLOR + str(self.charcolor) + char)[::-1]):
                self.lines[y].insert(x, char)
        else:
            self.lines[y][x] = char
