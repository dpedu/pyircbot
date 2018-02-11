import pytest
from contextlib import closing
from tests.lib import pm
from tests.lib import *  # NOQA - fixtures

# TODO:
# - Responds to pms where the dest != the bot's nick


@pytest.fixture
def nickbot(fakebot):
    """
    Provide a bot loaded with the Nickuser module. Clear the database.
    """
    fakebot.loadmodule("SQLite")
    with closing(fakebot.moduleInstances["SQLite"].opendb("attributes.db")) as db:
        for table in ["attribute", "items", "values"]:
            db.query("DROP TABLE IF EXISTS `{}`;".format(table))
    fakebot.loadmodule("AttributeStorageLite")
    fakebot.loadmodule("NickUser")
    return fakebot


def test_blind_login(nickbot):
    pm(nickbot, ".login foobar")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.login: You must first set a password with .setpass')


def test_no_pms(nickbot):
    nickbot.feed_line(".login foobar")
    nickbot.act_PRIVMSG.assert_not_called()


def test_register(nickbot):
    pm(nickbot, ".setpass")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.setpass: usage: ".setpass newpass" or ".setpass oldpass newpass"')
    nickbot.act_PRIVMSG.reset_mock()
    pm(nickbot, ".setpass foobar")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.setpass: Your password has been set to "foobar".')
    nickbot.act_PRIVMSG.reset_mock()


def test_register_login(nickbot):
    test_register(nickbot)
    pm(nickbot, ".login")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.login: usage: ".login password"')
    nickbot.act_PRIVMSG.reset_mock()
    pm(nickbot, ".login foobar")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.login: You have been logged in from: cia.gov')
    nickbot.act_PRIVMSG.reset_mock()


def test_badpass(nickbot):
    test_register(nickbot)
    pm(nickbot, ".login oopsie")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.login: incorrect password.')


def test_change_needspass(nickbot):
    test_register(nickbot)
    pm(nickbot, ".setpass oopsie")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.setpass: You must provide the old password when setting a new one.')


def test_logout(nickbot):
    test_register_login(nickbot)
    pm(nickbot, ".logout")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.logout: You have been logged out.')
    nickbot.act_PRIVMSG.reset_mock()
    pm(nickbot, ".logout")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.logout: You must first be logged in')


def test_changepass(nickbot):
    test_register_login(nickbot)
    pm(nickbot, ".setpass foobar newpass")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.setpass: Your password has been set to "newpass".')
    nickbot.act_PRIVMSG.reset_mock()
    pm(nickbot, ".setpass wrong newpass2")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.setpass: Old password incorrect.')


def test_check(nickbot):
    test_register_login(nickbot)
    mod = nickbot.moduleInstances["NickUser"]
    assert mod.check("chatter", "cia.gov")
    assert not mod.check("chatter", "not-valid.hostname")
    pm(nickbot, ".logout")
    assert not mod.check("chatter", "cia.gov")
