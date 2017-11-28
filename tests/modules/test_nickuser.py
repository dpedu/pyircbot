import pytest
from contextlib import closing
from tests.lib import *  # NOQA - fixtures

# TODO:
# - Responds to pms where the dest != the bot's nick


@pytest.fixture
def nickbot(fakebot):
    """
    Provide a bot loaded with the Calc module. Clear the database.
    """
    fakebot.botconfig["module_configs"]["Calc"] = {
        "allowDelete": True,
        "delaySubmit": 0,
        "delayCalc": 0,
        "delayCalcSpecific": 0,
        "delayMatch": 0}
    fakebot.loadmodule("SQLite")
    with closing(fakebot.moduleInstances["SQLite"].opendb("attributes.db")) as db:
        for q in ["DELETE FROM attribute;",
                  "DELETE FROM items;",
                  "DELETE FROM `values`;"]:
            db.query(q)
    fakebot.loadmodule("AttributeStorageLite")
    fakebot.loadmodule("NickUser")
    return fakebot


def pm(nickbot, line):
    nickbot.feed_line(line, args=['bot'])


def test_blind_login(nickbot):
    pm(nickbot, ".login foobar")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.login: You must first set a password with .setpass')


def test_register(nickbot):
    pm(nickbot, ".setpass foobar")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.setpass: Your password has been set to "foobar".')
    nickbot.act_PRIVMSG.reset_mock()


def test_register_login(nickbot):
    test_register(nickbot)
    pm(nickbot, ".login foobar")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.login: You have been logged in from: cia.gov')
    nickbot.act_PRIVMSG.reset_mock()


def test_badpass(nickbot):
    test_register(nickbot)
    pm(nickbot, ".login oopsie")
    nickbot.act_PRIVMSG.assert_called_once_with('chatter', '.login: incorrect password.')


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
