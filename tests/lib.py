import os
import sys
import pytest
from threading import Thread
from random import randint
from pyircbot import PyIRCBot
from pyircbot.pyircbot import PrimitiveBot
from pyircbot.irccore import IRCEvent, UserPrefix, IRCCore
from unittest.mock import MagicMock
from tests.miniircd import Server as MiniIrcServer


sys.path.append(os.path.join(os.path.dirname(__file__), "../pyircbot/modules/"))


class FakeBaseBot(PrimitiveBot):
    """
    Class that simulates a bot base class. You need to add mocks for any methods you expect called, beyond privmsg.
    """

    def __init__(self, config):
        super().__init__(config)
        self.act_PRIVMSG = MagicMock()
        self._modules = []

    def feed_line(self, trailing, cmd="PRIVMSG", args=["#test"], sender=("chatter", "root", "cia.gov")):
        """
        Feed a message into the bot.
        """
        msg = IRCCore.packetAsObject(cmd,
                                     args,
                                     f"{sender[0]}!{sender[1]}@{sender[2]}",   # hack
                                     trailing)

        for module_name, module in self.moduleInstances.items():# TODO dedupe this block across the various base classes
            for hook in module.irchooks:
                validation = hook.validator(msg, self)
                if validation:
                    hook.method(msg, validation)

    def closeAllModules(self):
        for modname in self._modules:
            self.unloadmodule(modname)

    def loadmodule(self, module_name):
        super().loadmodule(module_name)
        self._modules.append(module_name)

    def unloadmodule(self, module_name):
        super().unloadmodule(module_name)
        self._modules.remove(module_name)

    def get_nick(self):
        return "testbot"


@pytest.fixture
def fakebot(tmpdir):
    # TODO copy data tree to isolated place so each fakebot() is isolated
    os.mkdir(os.path.join(tmpdir, "data"))
    bot = FakeBaseBot({"bot": {"datadir": tmpdir},
                       "module_configs": {}})
    yield bot
    bot.closeAllModules()


@pytest.fixture
def ircserver():
    """
    Fixture providing an isolated IRC server.

    :return: tuple of (port, server_object)
    """
    port = randint(40000, 65000)

    class IRCOptions(object):
        channel_log_dir = None
        chroot = None
        daemon = None
        debug = None
        ipv6 = None
        listen = "127.0.0.1"
        log_count = 10
        log_file = None
        log_max_size = 10
        motd = None
        password = None
        password_file = None
        pid_file = None
        ports = [port]
        setuid = None
        ssl_pem_file = None
        state_dir = None
        verbose = None

    server = MiniIrcServer(IRCOptions)
    server_t = Thread(target=server.start, daemon=True)
    server_t.start()
    yield port, server
    server.stop()


@pytest.fixture
def livebot(ircserver, tmpdir):
    """
    A full-fledged bot connected to an irc server.
    """
    port, server = ircserver
    channel = "#test" + str(randint(100000, 1000000))
    nick = "testbot" + str(randint(100000, 1000000))
    config = {
        "bot": {
            "datadir": tmpdir,
            "rpcbind": "0.0.0.0",
            "rpcport": -1,
            "usermodules": []
        },
        "connection": {
            "servers": [
                ["localhost", port]
            ],
            "force_ipv6": False,
            "rate_limit": {
                "rate_max": 5.0,
                "rate_int": 1.1
            }
        },
        "modules": [
            "PingResponder",
            "Services"
        ],
        "module_configs": {
            "Services": {
                "user": {
                    "nick": [
                        nick,
                        nick + "_",
                        nick + "__"
                    ],
                    "password": "nickservpassword",
                    "username": "pyircbot3",
                    "hostname": "pyircbot3.domain.com",
                    "realname": "pyircbot3"
                },
                "ident": {
                    "enable": "no",
                    "to": "nickserv",
                    "command": "identify %(password)s",
                    "ghost": "no",
                    "ghost_to": "nickserv",
                    "ghost_cmd": "ghost %(nick)s %(password)s"
                },
                "channels": [
                    channel
                ],
                "privatechannels": {
                    "to": "chanserv",
                    "command": "invite %(channel)s",
                    "list": []
                }
            }
        }
    }

    bot = PyIRCBot(config)
    bot_t = Thread(target=bot.run, daemon=True)
    # bot_t.start()
    yield port, server, bot, bot_t, channel, nick

    bot.kill(message="bye", forever=True)


def pm(bot, line, nick="chatter"):
    bot.feed_line(line, args=['bot'], sender=(nick, "root", "cia.gov"))
