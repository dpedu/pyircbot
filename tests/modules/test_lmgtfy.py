import pytest
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def googbot(fakebot):
    """
    Provide a bot loaded with the LMGTFY module
    """
    fakebot.loadmodule("LMGTFY")
    return fakebot


def test_lmgtfy_basic(googbot):
    googbot.feed_line(".lmgtfy foobar asdf")
    googbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: http://lmgtfy.com/?q=foobar+asdf')
