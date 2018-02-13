import pytest
from tests.lib import *  # NOQA - fixtures
from unittest.mock import call


@pytest.fixture
def helpbot(fakebot):
    """
    Provide a bot loaded with the ModInfo module
    """
    fakebot.loadmodule("ModInfo")
    return fakebot


def test_helpindex(helpbot):
    helpbot.feed_line(".helpindex")
    helpbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: commands: .help, .helpindex')


def test_help(helpbot):
    helpbot.feed_line(".help")
    helpbot.act_PRIVMSG.assert_has_calls(
        [call('#test', 'ModInfo .help [command] show the manual for all or [commands] '),
         call('#test', 'ModInfo .helpindex      show a short list of all commands     ')],
        any_order=True)


def test_help_one(helpbot):
    helpbot.feed_line(".help .helpindex")
    helpbot.act_PRIVMSG.assert_called_once_with('#test',
                                                'RTFM: .helpindex: (.helpindex) show a short list of all commands')
