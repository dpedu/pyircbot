import os
import sys
import pytest
from random import randint
from threading import Thread
from pyircbot.pyircbot import PrimitiveBot
from pyircbot.irccore import IRCEvent, UserPrefix
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

    def feed_line(self, trailing, cmd="PRIVMSG", args=["#test"], sender=("chatter", "root", "cia.gov")):
        """
        Feed a message into the bot.
        """
        msg = IRCEvent(cmd,
                       args,
                       UserPrefix(*sender),
                       trailing)

        for module_name, module in self.moduleInstances.items():# TODO dedupe this block across the various base classes
            for hook in module.irchooks:
                validation = hook.validator(msg, self)
                if validation:
                    hook.method(msg, validation)


@pytest.fixture
def fakebot():
    # TODO copy data tree to isolated place so each fakebot() is isolated
    bot = FakeBaseBot({"bot": {"datadir": "./examples/data/"},
                       "module_configs": {}})
    yield bot


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
