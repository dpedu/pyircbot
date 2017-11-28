import pytest
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def bot(fakebot):
    fakebot.loadmodule("ModInfo")
    return fakebot


def test_help(bot):
    bot.feed_line(".help")
    bot.act_PRIVMSG.assert_called_once_with('#test',
                                            'ModInfo: .help [command]    show the manual for all or [commands]')


def test_helpindex(bot):
    bot.feed_line(".helpindex")
    bot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: commands: .help')
