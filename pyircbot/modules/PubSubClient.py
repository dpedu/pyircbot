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
                tag, subcommand, message = message.split(" ", 2)
                if tag != "default":
                    continue

                if subcommand == "privmsg":
                    dest, message = loads(message)
                    self.bot.act_PRIVMSG(dest, message)
            except:
                print_exc()

    def publish(self, subchannel, message):
        self.bus.pub(self.config.get("publish").format(subchannel), "{} {}".format("default", message))

    @hook("PRIVMSG")
    def bus_privmsg(self, msg):
        # msg.command msg.args msg.prefix msg.trailing
        self.publish("privmsg", dumps([msg.args, msg.prefix[0], msg.trailing, {"prefix": msg.prefix}]))

    @hook("JOIN")
    def bus_join(self, msg):
        # msg.command msg.args msg.prefix msg.trailing
        self.publish("join", dumps([msg.prefix[0], msg.trailing, {"prefix": msg.prefix}]))

    @hook("PART")
    def bus_part(self, msg):
        # msg.command msg.args msg.prefix msg.trailing
        self.publish("part", dumps([msg.args, msg.prefix[0], msg.trailing, {"prefix": msg.prefix}]))

    @hook("PRIVMSG")
    def bus_command(self, msg):
        # msg.command msg.args msg.prefix msg.trailing
        # self.publish("privmsg", dumps([msg.args, msg.prefix[0], msg.trailing, {"prefix": msg.prefix}]))
        match = COMMAND_RE.match(msg.trailing)
        if match:
            cmd_name = match.groups()[1]
            cmd_args = msg.trailing[len(cmd_name) + 1:].strip()
            self.publish("command_{}".format(cmd_name),
                         dumps([msg.args, msg.prefix[0], cmd_args, {"prefix": msg.prefix}]))

    def onenable(self):
        self.bus = MsgbusSubClient(self.host, int(self.port))
        for channel in self.config.get("subscriptions"):
            self.bus.sub(channel)
        self.publish("sys", "online")

    def ondisable(self):
        self.log.warning("clean it up")
        self.publish("sys", "offline")
        self.bus.close()

"""

Bot connects to the bus:

    pyircbot_sys default online

Bot disconnects from the bus:

    pyircbot_sys default offline

Bot relaying a privmsg:

    pyircbot_privmsg default [["#clonebot"], "dave-irccloud", "message text",
                              {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

User parts a channel:

    pyircbot_part default [["#clonebot"], "dave-irccloud", "part msg",
                           {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

User joins a channel:

    pyircbot_join default ["dave-irccloud", "#clonebot",
                           {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

User uses the command `.seen testbot`:

    pyircbot_command_seen default [["#clonebot"], "dave-irccloud", "testbot",
                                   {"prefix": ["dave-irccloud", "sid36094", "Clk-247B1F43.irccloud.com"]}]

# Client sending a message that the bot will relay

    pyircbot_send default privmsg ["#clonebot", "asdf1234"]

"""
