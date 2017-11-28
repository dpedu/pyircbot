import os
import sys
import pytest
from pyircbot.pyircbot import PrimitiveBot
from pyircbot.irccore import IRCEvent, UserPrefix
from unittest.mock import MagicMock


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
    bot = FakeBaseBot({"bot": {"datadir": "./examples/data/"},
                       "module_configs": {}})
    return bot
