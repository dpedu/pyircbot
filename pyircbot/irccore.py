"""
.. module:: IRCCore
   :synopsis: IRC protocol class

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import socket
import asynchat
import asyncore
import logging
import traceback
import sys
from socket import SHUT_RDWR

try:
    from cStringIO import StringIO
except:
    from io import BytesIO as StringIO

class IRCCore(asynchat.async_chat):
    
    def __init__(self):
        asynchat.async_chat.__init__(self)
        
        self.connected=False
        """If we're connected or not"""
        
        self.log = logging.getLogger('IRCCore')
        """Reference to logger object"""
        
        self.buffer = StringIO()
        """cStringIO used as a buffer"""
        
        self.alive = True
        """True if we should try to stay connected"""
        
        self.server = None
        """Server address"""
        self.port = 0
        """Server port"""
        self.ipv6 = False
        """Use IPv6?"""
        
        # IRC Messages are terminated with \r\n
        self.set_terminator(b"\r\n")
        
        # Set up hooks for modules
        self.initHooks()
        
        # Map for asynchat
        self.asynmap = {}
    
    def loop(self):
        asyncore.loop(map=self.asynmap)
    
    def kill(self):
        """TODO close the socket"""
        self.act_QUIT("Help! Another thread is killing me :(")
    
    " Net related code here on down "
    
    def getBuf(self):
        """Return the network buffer and clear it"""
        self.buffer.seek(0)
        data = self.buffer.read()
        self.buffer = StringIO()
        return data
    
    def collect_incoming_data(self, data):
        """Recieve data from the IRC server, append it to the buffer
        
        :param data: the data that was recieved
        :type data: str"""
        #self.log.debug("<< %(message)s", {"message":repr(data)})
        self.buffer.write(data)
    
    def found_terminator(self):
        """A complete command was pushed through, so clear the buffer and process it."""
        line = None
        buf = self.getBuf()
        try:
            line = buf.decode("UTF-8")
        except UnicodeDecodeError as ude:
            self.log.error("found_terminator(): could not decode input as UTF-8")
            self.log.error("found_terminator(): data: %s" % line)
            self.log.error("found_terminator(): repr(data): %s" % repr(line))
            self.log.error("found_terminator(): error: %s" % str(ude))
            return
        self.process_data(line)
    
    def handle_close(self):
        """Called when the socket is disconnected. Triggers the _DISCONNECT hook"""
        self.log.debug("handle_close")
        self.connected=False
        self.close()
        self.fire_hook("_DISCONNECT")
    
    def handle_error(self, *args, **kwargs):
        """Called on fatal network errors."""
        self.log.error("Connection failed (handle_error)")
        self.log.error(str(args))
        self.log.error(str(kwargs))
        self.log(IRCCore.trace());
    
    def _connect(self):
        """Connect to IRC"""
        self.log.debug("Connecting to %(server)s:%(port)i", {"server":self.server, "port":self.port})
        socket_type = socket.AF_INET
        if self.ipv6:
            self.log.info("IPv6 is enabled.")
            socket_type = socket.AF_INET6
        socketInfo = socket.getaddrinfo(self.server, self.port, socket_type)
        self.create_socket(socket_type, socket.SOCK_STREAM)
        
        self.connect(socketInfo[0][4])
        self.asynmap[self._fileno] = self # http://willpython.blogspot.com/2010/08/multiple-event-loops-with-asyncore-and.html
    
    def handle_connect(self):
        """When asynchat indicates our socket is connected, fire the _CONNECT hook"""
        self.connected=True
        self.log.debug("handle_connect: connected")
        self.fire_hook("_CONNECT")
        self.log.debug("handle_connect: complete")
    
    def sendRaw(self, text):
        """Send a raw string to the IRC server
        
        :param text: the string to send
        :type text: str"""
        if self.connected:
            #self.log.debug(">> "+text)
            self.send( (text+"\r\n").encode("UTF-8").decode().encode("UTF-8"))
        else:
            self.log.warning("Send attempted while disconnected. >> "+text)
    
    def process_data(self, data):
        """Process one line of tet irc sent us
        
        :param data: the data to process
        :type data: str"""
        if data.strip() == "":
            return
            
        prefix = None
        command = None
        args=[]
        trailing=None
        
        if data[0]==":":
            prefix=data.split(" ")[0][1:]
            data=data[data.find(" ")+1:]
        command = data.split(" ")[0]
        data=data[data.find(" ")+1:]
        if(data[0]==":"):
            # no args
            trailing = data[1:].strip()
        else:
            trailing = data[data.find(" :")+2:].strip()
            data = data[:data.find(" :")]
            args = data.split(" ")
        for index,arg in enumerate(args):
            args[index]=arg.strip()
        if not command in self.hookcalls:
            self.log.warning("Unknown command: cmd='%s' prefix='%s' args='%s' trailing='%s'" % (command, prefix, args, trailing))
        else:
            self.fire_hook(command, args=args, prefix=prefix, trailing=trailing)
    
    
    " Module related code "
    def initHooks(self):
        """Defines hooks that modules can listen for events of"""
        self.hooks = [
            '_CONNECT', # Called when the bot connects to IRC on the socket level
            '_DISCONNECT', # Called when the irc socket is forcibly closed
            'NOTICE',    # :irc.129irc.com NOTICE AUTH :*** Looking up your hostname...
            'MODE',        # :CloneABCD MODE CloneABCD :+iwx
            'PING',        # PING :irc.129irc.com
            'JOIN',        # :CloneA!dave@hidden-B4F6B1AA.rit.edu JOIN :#clonea
            'QUIT',        # :HCSMPBot!~HCSMPBot@108.170.48.18 QUIT :Quit: Disconnecting!
            'NICK',        # :foxiAway!foxi@irc.hcsmp.com NICK :foxi
            'PART',        # :CloneA!dave@hidden-B4F6B1AA.rit.edu PART #clonea
            'PRIVMSG',    # :CloneA!dave@hidden-B4F6B1AA.rit.edu PRIVMSG #clonea :aaa
            'KICK',        # :xMopxShell!~rduser@host KICK #xMopx2 xBotxShellTest :xBotxShellTest
            'INVITE',    # :gmx!~gmxgeek@irc.hcsmp.com INVITE Tyrone :#hcsmp'
            '001',        # :irc.129irc.com 001 CloneABCD :Welcome to the 129irc IRC Network CloneABCD!CloneABCD@djptwc-laptop1.rit.edu
            '002',        # :irc.129irc.com 002 CloneABCD :Your host is irc.129irc.com, running version Unreal3.2.8.1
            '003',        # :irc.129irc.com 003 CloneABCD :This server was created Mon Jul 19 2010 at 03:12:01 EDT
            '004',        # :irc.129irc.com 004 CloneABCD irc.129irc.com Unreal3.2.8.1 iowghraAsORTVSxNCWqBzvdHtGp lvhopsmntikrRcaqOALQbSeIKVfMCuzNTGj
            '005',        # :irc.129irc.com 005 CloneABCD CMDS=KNOCK,MAP,DCCALLOW,USERIP UHNAMES NAMESX SAFELIST HCN MAXCHANNELS=10 CHANLIMIT=#:10 MAXLIST=b:60,e:60,I:60 NICKLEN=30 CHANNELLEN=32 TOPICLEN=307 KICKLEN=307 AWAYLEN=307 :are supported by this server
            '250',        # :chaos.esper.net 250 xBotxShellTest :Highest connection count: 1633 (1632 clients) (186588 connections received)
            '251',        # :irc.129irc.com 251 CloneABCD :There are 1 users and 48 invisible on 2 servers
            '252',        # :irc.129irc.com 252 CloneABCD 9 :operator(s) online
            '254',        # :irc.129irc.com 254 CloneABCD 6 :channels formed
            '255',        # :irc.129irc.com 255 CloneABCD :I have 42 clients and 1 servers
            '265',        # :irc.129irc.com 265 CloneABCD :Current Local Users: 42  Max: 47
            '266',        # :irc.129irc.com 266 CloneABCD :Current Global Users: 49  Max: 53
            '332',        # :chaos.esper.net 332 xBotxShellTest #xMopx2 :/ #XMOPX2 / https://code.google.com/p/pyircbot/ (Channel Topic)
            '333',        # :chaos.esper.net 333 xBotxShellTest #xMopx2 xMopxShell!~rduser@108.170.60.242 1344370109
            '353',        # :irc.129irc.com 353 CloneABCD = #clonea :CloneABCD CloneABC 
            '366',        # :irc.129irc.com 366 CloneABCD #clonea :End of /NAMES list.
            '372',        # :chaos.esper.net 372 xBotxShell :motd text here
            '375',        # :chaos.esper.net 375 xBotxShellTest :- chaos.esper.net Message of the Day -
            '376',        # :chaos.esper.net 376 xBotxShell :End of /MOTD command.
            '422',        # :irc.129irc.com 422 CloneABCD :MOTD File is missing
            '433',        # :nova.esper.net 433 * pyircbot3 :Nickname is already in use.
        ]
        " mapping of hooks to methods "
        self.hookcalls = {}
        for command in self.hooks:
            self.hookcalls[command]=[]
    
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
        
        for hook in self.hookcalls[command]:
            try:
                hook(args, prefix, trailing)
            except:
                self.log.warning("Error processing hook: \n%s"% self.trace())
    
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
    
    " Utility methods "
    @staticmethod
    def decodePrefix(prefix):
        """Given a prefix like nick!username@hostname, return an object with these properties
        
        :param prefix: the prefix to disassemble
        :type prefix: str
        :returns: object -- an UserPrefix object with the properties `nick`, `username`, `hostname` or a ServerPrefix object with the property `hostname`"""
        if "!" in prefix:
            ob = type('UserPrefix', (object,), {})
            ob.nick, prefix = prefix.split("!")
            ob.username, ob.hostname = prefix.split("@")
            return ob
        else:
            ob = type('ServerPrefix', (object,), {})
            ob.hostname = prefix
            return ob
    
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
    def act_PONG(self, data):
        """Use the `/pong` command - respond to server pings
        
        :param data: the string or number the server sent with it's ping
        :type data: str"""
        self.sendRaw("PONG :%s" % data)
    
    def act_USER(self, username, hostname, realname):
        """Use the USER protocol command. Used during connection
        
        :param username: the bot's username
        :type username: str
        :param hostname: the bot's hostname
        :type hostname: str
        :param realname: the bot's realname
        :type realname: str"""
        self.sendRaw("USER %s %s %s :%s" % (username, hostname, self.server, realname))
    
    def act_NICK(self, newNick):
        """Use the `/nick` command
        
        :param newNick: new nick for the bot
        :type newNick: str"""
        self.nick = newNick
        self.sendRaw("NICK %s" % newNick)
    
    def act_JOIN(self, channel):
        """Use the `/join` command
        
        :param channel: the channel to attempt to join
        :type channel: str"""
        self.sendRaw("JOIN %s"%channel)
    
    def act_PRIVMSG(self, towho, message):
        """Use the `/msg` command
        
        :param towho: the target #channel or user's name
        :type towho: str
        :param message: the message to send
        :type message: str"""
        self.sendRaw("PRIVMSG %s :%s"%(towho,message))
    
    def act_MODE(self, channel, mode, extra=None):
        """Use the `/mode` command
        
        :param channel: the channel this mode is for
        :type channel: str
        :param mode: the mode string. Example: +b
        :type mode: str
        :param extra: additional argument if the mode needs it. Example: user@*!*
        :type extra: str"""
        if extra != None:
            self.sendRaw("MODE %s %s %s" % (channel,mode,extra))
        else:
            self.sendRaw("MODE %s %s" % (channel,mode))
    
    def act_ACTION(self, channel, action):
        """Use the `/me <action>` command
        
        :param channel: the channel name or target's name the message is sent to
        :type channel: str
        :param action: the text to send
        :type action: str"""
        self.sendRaw("PRIVMSG %s :\x01ACTION %s"%(channel,action))
    
    def act_KICK(self, channel, who, comment=""):
        """Use the `/kick <user> <message>` command
        
        :param channel: the channel from which the user will be kicked
        :type channel: str
        :param who: the nickname of the user to kick
        :type action: str
        :param comment: the kick message
        :type comment: str"""
        self.sendRaw("KICK %s %s :%s" % (channel, who, comment))
    
    def act_QUIT(self, message):
        """Use the `/quit` command
        
        :param message: quit message
        :type message: str"""
        self.sendRaw("QUIT :%s" % message)
    
