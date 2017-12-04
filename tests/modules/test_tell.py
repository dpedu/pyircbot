import pytest
from contextlib import closing
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def tellbot(fakebot):
    """
    Provide a bot loaded with the Calc module. Clear the database.
    """
    fakebot.botconfig["module_configs"]["Tell"] = {"max": 10, "maxage": 2678400}
    fakebot.loadmodule("SQLite")
    with closing(fakebot.moduleInstances["SQLite"].opendb("tell.db")) as db:
        db.query("DROP TABLE IF EXISTS tells;")
    fakebot.loadmodule("Tell")
    return fakebot


def test_addtell(tellbot):
    tellbot.feed_line(".tell fudge foo")
    tellbot.act_PRIVMSG.assert_called_once_with("#test", "chatter: I'll pass that along.")
    tellbot.act_PRIVMSG.reset_mock()


def test_gettell(tellbot):
    test_addtell(tellbot)
    tellbot.feed_line(".", sender=("fudge", "user", "host"))
    tellbot.act_PRIVMSG.assert_called_once_with("#test", "fudge: chatter said 0 minutes ago: foo")


def test_tellhelp(tellbot):
    tellbot.feed_line(".tell")
    tellbot.act_PRIVMSG.assert_called_once_with("#test", "chatter: .tell <person> <message> - Tell someone something the next time they're seen. Example: .tell antiroach Do your homework!")


def test_max(tellbot):
    for _ in range(0, 10):
        tellbot.feed_line(".tell foobar asdf")
    tellbot.act_PRIVMSG.reset_mock()
    tellbot.feed_line(".tell foobar asdf")
    tellbot.act_PRIVMSG.assert_not_called()

