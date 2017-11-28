import pytest
from pyircbot.modules.Calc import Calc
from pyircbot.pyircbot import ModuleLoader


class FakeBaseBot(ModuleLoader):

    " IRC methods "
    def act_PRIVMSG(self, towho, message):
        """Use the `/msg` command

        :param towho: the target #channel or user's name
        :type towho: str
        :param message: the message to send
        :type message: str"""
        # self.sendRaw("PRIVMSG %s :%s" % (towho, message))
        print("act_PRIVMSG(towho={}, message={})".format(towho, message))


@pytest.fixture
def fakebot():
    bot = FakeBaseBot()
    bot.botconfig = {"bot": {"datadir": "./examples/data/"}}
    bot.loadmodule("SQLite")
    bot.loadmodule("Calc")
    return bot


def test_foo(fakebot):
    print(fakebot)
