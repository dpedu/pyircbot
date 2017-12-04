import pytest
from contextlib import closing
from tests.lib import *  # NOQA - fixtures
from time import sleep
import datetime


@pytest.fixture
def rbot(fakebot):
    """
    Provide a bot loaded with the Calc module. Clear the database.
    """
    fakebot.botconfig["module_configs"]["Remind"] = {"mytimezone": "US/Pacific", "precision": 0.2}
    fakebot.loadmodule("SQLite")
    with closing(fakebot.moduleInstances["SQLite"].opendb("remind.db")) as db:
        db.query("DROP TABLE IF EXISTS `reminders`;")
    fakebot.loadmodule("Remind")
    return fakebot


@pytest.mark.slow
def test_remind_in(rbot):
    rbot.feed_line(".in 3s frig off")
    rbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: Ok, talk to you in approx 0h0m')
    rbot.act_PRIVMSG.reset_mock()
    sleep(2.5)
    rbot.act_PRIVMSG.assert_not_called()
    sleep(1)
    rbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: Reminder: frig off')


@pytest.mark.slow
def test_remind_at(rbot):
    then = datetime.datetime.now() + datetime.timedelta(seconds=3)
    rbot.feed_line(".at {} frig off".format(then.strftime("%H:%M:%SPDT")))
    rbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: Ok, will do. Approx 0h0m to go.')
    rbot.act_PRIVMSG.reset_mock()
    sleep(2)
    rbot.act_PRIVMSG.assert_not_called()
    sleep(2)
    rbot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: Reminder: frig off')
