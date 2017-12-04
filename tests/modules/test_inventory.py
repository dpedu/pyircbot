import pytest
from contextlib import closing
from unittest.mock import call
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def invbot(fakebot):
    """
    Provide a bot loaded with the Calc module. Clear the database.
    """
    fakebot.botconfig["module_configs"]["Inventory"] = {
        "limit": 2,
        "recv_msg": "Oh, thanks, I'll keep %(adjective)s%(item)s safe",
        "inv_msg": "\u0001ACTION is carrying %(itemlist)s\u0001",
        "swap_msg": "\u0001ACTION takes %(adjective)s%(recv_item)s but drops %(drop_item)s\u0010",
        "dupe_msg": "No thanks, I've already got %(item)s",
        "adjectives": [
            "a",
            "some",
            "the",
            "an",
            "these"
        ]
    }
    fakebot.loadmodule("SQLite")
    with closing(fakebot.moduleInstances["SQLite"].opendb("inventory.db")) as db:
        db.query("DROP TABLE IF EXISTS `inventory`;")
    fakebot.loadmodule("Inventory")
    return fakebot


def test_inv_empty(invbot):
    invbot.feed_line(".inventory")
    invbot.act_PRIVMSG.assert_called_once_with('#test', '\x01ACTION is carrying nothing!\x01')


def test_inv_basic(invbot):
    invbot.feed_line(".have a foobar")
    invbot.act_PRIVMSG.assert_called_once_with('#test', "Oh, thanks, I'll keep this foobar safe")


def test_inv_full(invbot):
    invbot.feed_line(".have a foobarA")
    invbot.act_PRIVMSG.assert_called_once_with('#test', "Oh, thanks, I'll keep this foobarA safe")
    invbot.act_PRIVMSG.reset_mock()

    invbot.feed_line(".have a foobarB")
    invbot.act_PRIVMSG.assert_called_once_with('#test', "Oh, thanks, I'll keep this foobarB safe")
    invbot.act_PRIVMSG.reset_mock()

    invbot.feed_line(".inventory")
    invbot.act_PRIVMSG.assert_called_once_with('#test', "\x01ACTION is carrying foobarA, foobarB\x01")
    invbot.act_PRIVMSG.reset_mock()

    invbot.feed_line(".have a foobarC")
    assert invbot.act_PRIVMSG.mock_calls[0] == call('#test', '\x01ACTION takes a foobarC but drops foobarA\x10') \
        or invbot.act_PRIVMSG.mock_calls[0] == call('#test', '\x01ACTION takes a foobarC but drops foobarB\x10')
