from time import time
from math import floor
from json import load as json_load
from collections import namedtuple


ParsedCommand = namedtuple("ParsedCommand", "command args args_str message")


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


def messageHasCommand(command, message, requireArgs=False):
    """Check if a message has a command with or without args in it

    :param command: the command string to look for, like !ban. If a list is passed, the first match is returned.
    :type command: str or list
    :param message: the message string to look in, like "!ban Lil_Mac"
    :type message: str
    :param requireArgs: if true, only validate if the command use has any amount of trailing text
    :type requireArgs: bool"""

    if not type(command) == list:
        command = [command]
    for item in command:
        cmd = messageHasCommandSingle(item, message, requireArgs)
        if cmd:
            return cmd
    return False


def messageHasCommandSingle(command, message, requireArgs=False):
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

    if requireArgs and args == '':
        return False

    # Verified! Return the set.
    return ParsedCommand(command,
                         args.split(" ") if args else [],
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
