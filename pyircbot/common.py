from time import time
from math import floor
from json import load as json_load
from collections import namedtuple
from time import sleep
import os
from threading import Thread
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None


ParsedCommand = namedtuple("ParsedCommand", "command args args_str message")


def report(exception):
    if sentry_sdk:
        sentry_sdk.capture_exception(exception)


class burstbucket(object):
    def __init__(self, maximum, interval):
        """
        Burst bucket class for rate limiting
        :param maximum: maximum value in the bucket
        :param interval: how often a whole item is added to the bucket
        """
        # How many messages can be bursted
        self.bucket_max = maximum
        # how often the bucket has 1 item added
        self.bucket_period = interval
        # last time the burst bucket was filled
        self.bucket_lastfill = time()

        self.bucket = self.bucket_max

    def get(self):
        """
        Return 0 if no sleeping is necessary to rate limit. Otherwise, return the number of seconds to sleep. This
        method should be called again by the user after sleeping
        """
        # First, update the bucket
        # Check if $period time has passed since the bucket was filled
        since_fill = time() - self.bucket_lastfill
        if since_fill > self.bucket_period:
            # How many complete points are credited
            fills = floor(since_fill / self.bucket_period)
            self.bucket += fills
            if self.bucket > self.bucket_max:
                self.bucket = self.bucket_max
            # Advance the lastfill time appropriately
            self.bucket_lastfill += self.bucket_period * fills

        if self.bucket >= 1:
            self.bucket -= 1
            return 0
        return self.bucket_period - since_fill


class TouchReload(Thread):
    def __init__(self, filepaths, do, resolution=0.75):
        """
        Given a list of module files, call a lambda if the modification times changes
        :param filepaths: list of filepaths
        :param do: lambda to call with the altered filepath
        """
        super().__init__()
        self.files = [[os.path.normpath(i), None] for i in filepaths]
        self.do = do
        self.sleep = resolution

    def run(self):
        while True:
            for num, (path, mtime) in enumerate(self.files):
                new_mtime = os.stat(path).st_mtime
                if mtime is None:
                    self.files[num][1] = new_mtime
                    continue
                if mtime != new_mtime:
                    self.files[num][1] = new_mtime
                    self.do(path)
            sleep(self.sleep)


def messageHasCommand(command, message, requireArgs=False, withHighlight=False):
    """
    Check if a message has a command with or without args in it

    :param command: the command string to look for, like !ban. If a list is passed, the first match is returned.
    :type command: str or list
    :param message: the message string to look in, like "!ban Lil_Mac"
    :type message: str
    :param requireArgs: only match if trailing data is passed with the command used. False-like values disable This
        requirement. True-like values require any number of args greater than one. Int values require a specific number
        of args
    :type requireArgs: bool
    :param withHighlight: if provided, treat 'Nick[:,] command args' the same as '.command args' where Nick is a string
        provided by withHighlight
    :type withHighlight: str
    """

    if not type(command) == list:
        command = [command]
    for item in command:
        cmd = messageHasCommandSingle(item, message, requireArgs, withHighlight)
        if cmd:
            return cmd
    return False


def messageHasCommandSingle(command, message, requireArgs=False, withHighlight=False):
    if withHighlight:
        if message.startswith(withHighlight + ": ") or message.startswith(withHighlight + ", "):
            message = "." + message[len(withHighlight) + 2:]
    # Check if the message at least starts with the command
    messageBeginning = message[0:len(command)]
    if messageBeginning != command:
        return False
    # Make sure it's not a subset of a longer command (ie .meme being set off by .memes)
    subsetCheck = message[len(command):len(command) + 1]
    if subsetCheck != " " and subsetCheck != "":
        return False

    # We've got the command! Do we need args?
    argsStart = len(command)
    args = ""
    if argsStart > 0:
        args = message[argsStart + 1:].strip()
    args_list = args.split()
    if requireArgs:
        if args == '':
            return False
        elif type(requireArgs) is int and len(args_list) != requireArgs:
            return False

    # Verified! Return the set.
    return ParsedCommand(command,
                         args_list,
                         args,
                         message)


def load(filepath):
    """Return an object from the passed filepath

    :param filepath: path to a json file. filename must end with .json
    :type filepath: str
    :Returns:    | dict
    """

    if filepath.endswith(".json"):
        with open(filepath, 'r') as f:
            return json_load(f)
    else:
        raise Exception("Unknown config format")


def parse_irc_line(data):
    """
    Process one line of text irc sent us.

    Return tuple of (command, args, prefix, trailing)

    :param data: the data to process
    :type data: str
    :return tuple:"""
    if data.strip() == "":
        return

    prefix = None
    command = None
    args = []
    trailing = None

    if data[0] == ":":
        prefix = data.split(" ")[0][1:]
        data = data[data.find(" ") + 1:]
    command = data.split(" ")[0]
    data = data[data.find(" ") + 1:]
    if(data[0] == ":"):
        # no args
        trailing = data[1:].strip()
    else:
        # find trailing
        pos = data.find(" :")
        if pos == -1:
            trailing = None
        else:
            trailing = data[pos + 2:].strip()
            data = data[:data.find(" :")]
        args = data.split(" ")
    for index, arg in enumerate(args):
        args[index] = arg.strip()

    return (command, args, prefix, trailing)
