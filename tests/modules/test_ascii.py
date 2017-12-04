import os
import pytest
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def bot(fakebot):
    fakebot.botconfig["module_configs"]["ASCII"] = {
        "line_delay": 1.1,
        "allow_parallel": False,
        "allow_hilight": True,
        "list_max": 15
    }
    adir = os.path.join(fakebot.botconfig["bot"]["datadir"], "data", "ASCII")
    os.makedirs(adir, exist_ok=True)
    with open(os.path.join(adir, "test.txt"), "w") as f:
        f.write("hello world!")
    fakebot.loadmodule("ASCII")
    return fakebot


def test_ascii(bot):
    bot.feed_line(".ascii test")
    bot.act_PRIVMSG.assert_called_once_with('#test', 'hello world!')


def test_listascii(bot):
    bot.feed_line(".listascii")
    bot.act_PRIVMSG.assert_called_once_with('#test', 'Avalable asciis: test')
