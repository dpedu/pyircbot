import pytest
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def bot(fakebot):
    fakebot.loadmodule("ASCII")
    return fakebot


def test_ascii(bot):
    bot.feed_line(".ascii test")
    bot.act_PRIVMSG.assert_called_once_with('#test', 'hello world!')
