"""
.. module:: IRCCore
   :synopsis: IRC protocol class

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import socket
import asyncio
import logging
import traceback
import sys
from inspect import getargspec
from pyircbot.common import burstbucket, parse_irc_line, report
from collections import namedtuple
from io import StringIO
from time import time


IRCEvent = namedtuple("IRCEvent", "command args prefix trailing")
UserPrefix = namedtuple("UserPrefix", "nick username hostname")
ServerPrefix = namedtuple("ServerPrefix", "hostname")


class IRCCore(object):

    def __init__(self, servers, loop, rate_limit=True, rate_max=5.0, rate_int=1.1):
        self._loop = loop

        # rate limiting options
        self.rate_limit = rate_limit
        self.rate_max = float(rate_max)
        self.rate_int = float(rate_int)

        self.reconnect_delay = 3.0

        self.connected = False
        """If we're connected or not"""

        self.log = logging.getLogger('IRCCore')
        """Reference to logger object"""

        self.buffer = StringIO()
        """cStringIO used as a buffer"""

        self.alive = True
        """True if we should try to stay connected"""

        self.server = 0
        """Current server index"""
        self.servers = servers
        """List of server address"""
        self.port = 0
        """Server port"""
        self.connection_family = socket.AF_UNSPEC
        """Socket family. 0 will auto-detect ipv4 or v6. Change this to socket.AF_INET or socket.AF_INET6 force use of
           ipv4 or ipv6."""

        self.bind_addr = None
        """Optionally bind to a specific address. This should be a (host, port) tuple."""

        self.nick = None

        # Set up hooks for modules
        self.initHooks()

        self.outseq = 5
        self.outputq = asyncio.PriorityQueue()
        self._loop.call_soon_threadsafe(asyncio.ensure_future, self.outputqueue())

    async def loop(self, loop):
        while self.alive:
            try:
                # TODO support ipv6 again
                self.reader, self.writer = await asyncio.open_connection(self.servers[self.server][0],
                                                                         port=self.servers[self.server][1],
                                                                         loop=loop,
                                                                         ssl=None,
                                                                         family=self.connection_family,
                                                                         local_addr=self.bind_addr)
                self.fire_hook("_CONNECT")
            except (socket.gaierror, ConnectionRefusedError, OSError) as e:
                logging.warning("Non-fatal connect error, trying next server...")
                self.trace()
                report(e)
                self.server = (self.server + 1) % len(self.servers)
                await asyncio.sleep(1, loop=loop)
                continue
            while self.alive:
                try:
                    data = await self.reader.readuntil()
                    self.log.debug("<<< {}".format(repr(data)))
                    command, args, prefix, trailing = parse_irc_line(data.decode("UTF-8"))
                    self.fire_hook("_RECV", args=args, prefix=prefix, trailing=trailing)
                    if command not in self.hookcalls:
                        self.log.warning("Unknown command: cmd='{}' prefix='{}' args='{}' trailing='{}'"
                                         .format(command, prefix, args, trailing))
                    else:
                        self.fire_hook(command, args=args, prefix=prefix, trailing=trailing)
                except (ConnectionResetError, asyncio.streams.IncompleteReadError) as e:
                    self.trace()
                    report(e)
                    break
                except (UnicodeDecodeError, ) as e:
                    self.trace()
                    report(e)
            self.fire_hook("_DISCONNECT")
            self.writer.close()
            if self.alive:
                # TODO ramp down reconnect attempts
                logging.info("Reconnecting in {}s...".format(self.reconnect_delay))
                await asyncio.sleep(self.reconnect_delay)

    async def outputqueue(self):
        self.bucket = burstbucket(self.rate_max, self.rate_int)
        while True:
            # sleep until the bucket allows us to send
            # TODO warn/drop option if age (the _ above is older than some threshold)
            if self.rate_limit:
                while True:
                    s = self.bucket.get()
                    if s == 0:
                        break
                    else:
                        await asyncio.sleep(s, loop=self._loop)
            prio, _, line = await self.outputq.get()
            self.fire_hook('_SEND', args=None, prefix=None, trailing=None)
            self.log.debug(">>> {}".format(repr(line)))
            self.outputq.task_done()
            try:
                self.writer.write((line + "\r\n").encode("UTF-8"))
            except Exception as e:  # Probably fine if we drop messages while offline
                self.trace()
                report(e)

    async def kill(self, message="Help! Another thread is killing me :(", forever=True):
        """Send quit message, flush queue, and close the socket

        :param message: Quit message to send before disconnecting
        :type message: str
        """
        if forever:
            self.alive = False
        self.act_QUIT(message)  # TODO will this hang if the socket is having issues?
        await self.writer.drain()
        self.writer.close()
        self.log.info("Kill complete")

    def sendRaw(self, data, priority=None):
        """
        Send data on the wire. Lower priorities are sent first.
        :param data: unicode data to send. will be converted to utf-8
        :param priority: numerical priority value. If not None, the message will likely be sent first. Otherwise, an
                         ever-increasing sequence number is used to maintain order. For a minimum priority message,
                         use a priority value of sys.maxsize.
        """
        if priority is None:
            self.outseq += 1
            priority = self.outseq
        asyncio.run_coroutine_threadsafe(self.outputq.put((priority, time(), data, )), self._loop)

    " Module related code "
    def initHooks(self):
        """Defines hooks that modules can listen for events of"""
        self.hooks = [
            '_ALL',
            '_CONNECT',
            '_DISCONNECT',
            '_RECV',
            '_SEND',
            'NOTICE',
            'MODE',
            'PING',
            'JOIN',
            'QUIT',
            'NICK',
            'PART',
            'PRIVMSG',
            'KICK',
            'INVITE',
            '001',
            '002',
            '003',
            '004',
            '005',
            '250',
            '251',
            '252',
            '254',
            '255',
            '265',
            '266',
            '331',
            '332',
            '333',
            '353',
            '366',
            '372',
            '375',
            '376',
            '401',
            '422',
            '433',
        ]
        " mapping of hooks to methods "
        self.hookcalls = {command: [] for command in self.hooks}

    def fire_hook(self, command, args=None, prefix=None, trailing=None):
        """Run any listeners for a specific hook

        :param command: the hook to fire
        :type command: str
        :param args: the list of arguments, if any, the command was passed
        :type args: list
        :param prefix: prefix of the sender of this command
        :type prefix: str
        :param trailing: data payload of the command
        :type trailing: str"""
        for hook in self.hookcalls["_ALL"] + self.hookcalls[command]:
            try:
                if len(getargspec(hook).args) == 2:
                    hook(IRCCore.packetAsObject(command, args, prefix, trailing))
                else:
                    hook(args, prefix, trailing)

            except Exception as e:
                self.log.warning("Error processing hook: \n%s" % self.trace())
                report(e)

    def addHook(self, command, method):
        """**Internal.** Enable (connect) a single hook of a module

        :param command: command this hook will trigger on
        :type command: str
        :param method: callable method object to hook in
        :type method: object"""
        " add a single hook "
        if command in self.hooks:
            self.hookcalls[command].append(method)
        else:
            self.log.warning("Invalid hook - %s" % command)
            return False

    def removeHook(self, command, method):
        """**Internal.** Disable (disconnect) a single hook of a module

        :param command: command this hook triggers on
        :type command: str
        :param method: callable method that should be removed
        :type method: object"""
        " remove a single hook "
        if command in self.hooks:
            for hookedMethod in self.hookcalls[command]:
                if hookedMethod == method:
                    self.hookcalls[command].remove(hookedMethod)
        else:
            self.log.warning("Invalid hook - %s" % command)
            return False

    def packetAsObject(command, args, prefix, trailing):
        """Given an irc message's args, prefix, and trailing data return an object with these properties

        :param args: list of args from the IRC packet
        :type args: list
        :param prefix: prefix object parsed from the IRC packet
        :type prefix: ServerPrefix or UserPrefix
        :param trailing: trailing data from the IRC packet
        :type trailing: str
        :returns: object -- a IRCEvent object with the ``args``, ``prefix``, ``trailing``"""

        return IRCEvent(command, args,
                        IRCCore.decodePrefix(prefix) if prefix else None,
                        trailing)

    " Utility methods "
    @staticmethod
    def decodePrefix(prefix):
        """Given a prefix like nick!username@hostname, return an object with these properties

        :param prefix: the prefix to disassemble
        :type prefix: str
        :returns: object -- an UserPrefix object with the properties `nick`, `username`, `hostname` or a ServerPrefix
        object with the property `hostname`
        """
        if "!" in prefix:
            nick, prefix = prefix.split("!")
            username, hostname = prefix.split("@")
            return UserPrefix(nick, username, hostname)
        else:
            return ServerPrefix(prefix)

    @staticmethod
    def trace():
        """Return the stack trace of the bot as a string"""
        return traceback.format_exc()

    @staticmethod
    def fulltrace():
        """Return the stack trace of the bot as a string"""
        result = ""
        result += "\n*** STACKTRACE - START ***\n"
        code = []
        for threadId, stack in sys._current_frames().items():
            code.append("\n# ThreadID: %s" % threadId)
            for filename, lineno, name, line in traceback.extract_stack(stack):
                code.append('File: "%s", line %d, in %s' % (filename, lineno, name))
                if line:
                    code.append("  %s" % (line.strip()))
        for line in code:
            result += line + "\n"
        result += "\n*** STACKTRACE - END ***\n"
        return result

    " Data Methods "
    def get_nick(self):
        """Get the bot's current nick

        :returns: str - the bot's current nickname"""
        return self.nick

    " Action Methods "
    def act_PONG(self, data, priority=1):
        """Use the `/pong` command - respond to server pings

        :param data: the string or number the server sent with it's ping
        :type data: str"""
        self.sendRaw("PONG :%s" % data, priority)

    def act_USER(self, username, hostname, realname, priority=2):
        """Use the USER protocol command. Used during connection

        :param username: the bot's username
        :type username: str
        :param hostname: the bot's hostname
        :type hostname: str
        :param realname: the bot's realname
        :type realname: str"""
        self.sendRaw("USER %s %s %s :%s" % (username, hostname, self.servers[self.server], realname), priority)

    def act_NICK(self, newNick, priority=2):
        """Use the `/nick` command

        :param newNick: new nick for the bot
        :type newNick: str"""
        self.nick = newNick
        self.sendRaw("NICK %s" % newNick, priority)

    def act_JOIN(self, channel, priority=3):
        """Use the `/join` command

        :param channel: the channel to attempt to join
        :type channel: str"""
        self.sendRaw("JOIN %s" % channel, priority)

    def act_PRIVMSG(self, towho, message, priority=3):
        """Use the `/msg` command

        :param towho: the target #channel or user's name
        :type towho: str
        :param message: the message to send
        :type message: str"""
        self.sendRaw("PRIVMSG %s :%s" % (towho, message), priority)

    def act_MODE(self, channel, mode, extra=None, priority=2):
        """Use the `/mode` command

        :param channel: the channel this mode is for
        :type channel: str
        :param mode: the mode string. Example: +b
        :type mode: str
        :param extra: additional argument if the mode needs it. Example: user@*!*
        :type extra: str"""
        if extra is not None:
            self.sendRaw("MODE %s %s %s" % (channel, mode, extra), priority)
        else:
            self.sendRaw("MODE %s %s" % (channel, mode), priority)

    def act_ACTION(self, channel, action, priority=2):
        """Use the `/me <action>` command

        :param channel: the channel name or target's name the message is sent to
        :type channel: str
        :param action: the text to send
        :type action: str"""
        self.sendRaw("PRIVMSG %s :\x01ACTION %s" % (channel, action), priority)

    def act_KICK(self, channel, who, comment="", priority=2):
        """Use the `/kick <user> <message>` command

        :param channel: the channel from which the user will be kicked
        :type channel: str
        :param who: the nickname of the user to kick
        :type action: str
        :param comment: the kick message
        :type comment: str"""
        self.sendRaw("KICK %s %s :%s" % (channel, who, comment), priority)

    def act_QUIT(self, message, priority=2):
        """Use the `/quit` command

        :param message: quit message
        :type message: str"""
        self.sendRaw("QUIT :%s" % message, priority)

    def act_PASS(self, password, priority=1):
        """
        Send server password, for use on connection
        """
        self.sendRaw("PASS %s" % password, priority)
