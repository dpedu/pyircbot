import pytest
from contextlib import closing
from unittest.mock import call
from tests.lib import *  # NOQA - fixtures
import sqlite3


@pytest.fixture
def seenbot(fakebot):
    """
    Provide a bot loaded with the Seen module
    """
    fakebot.botconfig["module_configs"]["Seen"] = {
        "timezone": "UTC",
        "add_hours": 0
    }
    fakebot.loadmodule("Seen")
    return fakebot


def test_seen(seenbot):
    seenbot.feed_line("blah")
    seenbot.act_PRIVMSG.assert_not_called()
    dbpath = seenbot.moduleInstances["Seen"].getFilePath('database.sql3')
    seenbot.unloadmodule("Seen")

    with closing(sqlite3.connect(dbpath)) as db:
        with closing(db.cursor()) as c:
            c.execute("UPDATE `seen` SET `date`=1512369350.460798 WHERE `nick`='chatter';")
            assert c.rowcount == 1
            db.commit()

    seenbot.loadmodule("Seen")
    seenbot.feed_line(".seen chatter")
    seenbot.act_PRIVMSG.assert_called_once_with('#test', "I last saw chatter on 12/03/17 at 10:35 PM (UTC).")


def test_notseen(seenbot):
    seenbot.feed_line(".seen notme")
    seenbot.act_PRIVMSG.assert_called_once_with('#test', "Sorry, I haven't seen notme!")

