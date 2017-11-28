"""
.. module::PubSubClient
    :synopsis: connect to a message bus and act as a message relay
.. moduleauthor::Dave Pedu <dave@davepedu.com>
"""

from pyircbot.modulebase import ModuleBase, hook
from msgbus.client import MsgbusSubClient  # see http://gitlab.davepedu.com/dave/pymsgbus
from threading import Thread
from json import dumps, loads
from time import sleep
from zmq.error import Again
from traceback import print_exc
import re


COMMAND_RE = re.compile(r'\.(([a-zA-Z0-9]{1,16})(\s|$))(\s.+)?')


class PubSubClient(ModuleBase):
    def __init__(self, bot, moduleName):
        ModuleBase.__init__(self, bot, moduleName)
        self.host, self.port = self.config.get("servers")[0].split(":")
        self.bus = None
        self.bus_listener_thread = Thread(target=self.bus_listener)
        self.bus_listener_thread.daemon = True
        self.bus_listener_thread.start()

    def bus_listener(self):
        """
        Listen to the bus for send messages and act on recv
        """
        sleep(3)
        while True:#TODO clean exit onenable/ondisable etc
            if not self.bus:
                sleep(0.01)
                continue
            try:
                channel, message = self.bus.recv(block=False)
            except Again:
                sleep(0.01)
                continue
            try:
                print(channel, "--", message)
                name, subcommand, message = message.split(" ", 2)
                if name != self.config.get("name", "default") and name != "default":
                    continue
                if subcommand == "privmsg":
                    dest, message = loads(message)
                    self.bot.act_PRIVMSG(dest, message)
            except:
                print_exc()

    def publish(self, subchannel, message):
        """
        Abstracted callback for proxying irc messages to the bs
        :param subchannel: event type such as "privmsg"
        :type subchannel: str
        :param message: message body
        :type message: str
        """
        self.bus.pub(self.config.get("publish").format(subchannel), "{} {}".format("default", message))

    @hook("PRIVMSG")
    def bus_privmsg(self, msg, cmd):
        """
        Relay a privmsg to the event bus
        """
        self.publish("privmsg", dumps([msg.args, msg.prefix[0], msg.trailing, {"prefix": msg.prefix}]))

    @hook("JOIN")
    def bus_join(self, msg, cmd):
        """
        Relay a join message to the event bus
        """
        self.publish("join", dumps([msg.prefix[0], msg.trailing, {"prefix": msg.prefix}]))

    @hook("PART")
    def bus_part(self, msg, cmd):
        """
        Relay a part message to the event bus
        """
        self.publish("part", dumps([msg.args, msg.prefix[0], msg.trailing, {"prefix": msg.prefix}]))

    @hook("PRIVMSG")
    def bus_command(self, msg, cmd):
        """
        Parse commands and publish as separate channels on the bus. Commands like `.seen nick` will be published
        to channel `command_seen`.
        """
        match = COMMAND_RE.match(msg.trailing)
        if match:
            cmd_name = match.groups()[1]
            cmd_args = msg.trailing[len(cmd_name) + 1:].strip()
            self.publish("command_{}".format(cmd_name),
                         dumps([msg.args, msg.prefix[0], cmd_args, {"prefix": msg.prefix}]))

    def onenable(self):
        """
        Connect to the message bus when the module is enabled
        """
        self.bus = MsgbusSubClient(self.host, int(self.port))
        for channel in self.config.get("subscriptions"):
            self.bus.sub(channel)
        self.publish("sys", "online")

    def ondisable(self):
        """
        Disconnect to the message bus on shutdown
        """
        self.log.warning("clean it up")
        self.publish("sys", "offline")
        self.bus.close()
