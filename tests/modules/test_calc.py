import pytest
from contextlib import closing
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def calcbot(fakebot):
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
    with closing(fakebot.moduleInstances["SQLite"].opendb("calc.db")) as db:
        for q in ["DELETE FROM calc_addedby;",
                  "DELETE FROM calc_channels;",
                  "DELETE FROM calc_definitions;",
                  "DELETE FROM calc_words;"]:
            db.query(q)
    fakebot.loadmodule("Calc")
    return fakebot


def test_calc_empty(calcbot):
    calcbot.feed_line("calc")
    calcbot.act_PRIVMSG.assert_called_once_with('#test', 'This channel has no calcs, chatter :(')
    calcbot.act_PRIVMSG.reset_mock()


def test_calc_adds(calcbot):
    _add_fact(calcbot, "foo", "bar")
    _add_fact(calcbot, "foo2", "bar2")

    calcbot.feed_line(".quote foo2")
    calcbot.act_PRIVMSG.assert_called_once_with('#test', 'foo2 \x03= bar2 \x0314[added by: chatter]')
    calcbot.act_PRIVMSG.reset_mock()


def _add_fact(calcbot, fact, value):
    calcbot.feed_line("calc {} = {}".format(fact, value))
    calcbot.act_PRIVMSG.assert_called_once_with('#test', 'Thanks for the info, chatter.')
    calcbot.act_PRIVMSG.reset_mock()


def test_match(calcbot):
    _add_fact(calcbot, "xxx", "bar")
    _add_fact(calcbot, "yyy", "bar2")
    calcbot.feed_line(".match x")
    calcbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: 1 match (xxx\x03)')


def test_delete(calcbot):
    _add_fact(calcbot, "xxx", "bar")
    _add_fact(calcbot, "yyy", "bar2")
    calcbot.feed_line(".calc xxx =")
    calcbot.act_PRIVMSG.assert_called_once_with('#test', 'Calc deleted, chatter.')
    calcbot.act_PRIVMSG.reset_mock()
    calcbot.feed_line(".calc xxx")
    calcbot.act_PRIVMSG.assert_called_once_with('#test', "Sorry chatter, I don't know what 'xxx' is.")


def test_unicode(calcbot):
    _add_fact(calcbot, "👌👌👌", "uncode keys")
    _add_fact(calcbot, "uncode values", "👌👌👌")
    calcbot.feed_line(".calc 👌👌👌")
    calcbot.act_PRIVMSG.assert_called_once_with('#test', '👌👌👌 \x03= uncode keys \x0314[added by: chatter]')
    calcbot.act_PRIVMSG.reset_mock()
    calcbot.feed_line(".match 👌")
    calcbot.act_PRIVMSG.assert_called_once_with('#test', "chatter: 1 match (👌👌👌\x03)")


def test_delete_disable(calcbot):
    calcbot.botconfig["module_configs"]["Calc"]["allowDelete"] = False
    _add_fact(calcbot, "xxx", "bar")
    _add_fact(calcbot, "yyy", "bar2")
    calcbot.feed_line("calc xxx =")
    calcbot.act_PRIVMSG.assert_not_called()
