import pytest
from tests.lib import *  # NOQA - fixtures
from time import sleep, time
from pyircbot import IRCCore
import logging


logging.getLogger().setLevel(logging.DEBUG)


def wait_until(server, channel, nick, func, timeout):
    start = time()
    while time() < start + timeout:
        v = func()
        if v:
            return v
        sleep(0.02)
    raise Exception("Function {} did not settle after {}s".format(func, timeout))


def wait_until_joined(server, channel, nick, timeout=5.0):
    def in_ch():
        if channel in server.channels:
            members = [u.nickname for u in server.channels[channel].members]
            if nick in members:
                return members
    return wait_until(server, channel, nick, in_ch, timeout=timeout)


def wait_until_absent(server, channel, nick, timeout=5.0):
    def not_in_ch():
        if channel not in server.channels:
            return True
        members = [u.nickname for u in server.channels[channel].members]
        if nick not in members:
            return True
    return wait_until(server, channel, nick, not_in_ch, timeout=timeout)


def test_connect_and_join(livebot):
    port, server, bot, bot_t, channel, nick = livebot
    bot_t.start()
    assert nick in wait_until_joined(server, channel, nick)


@pytest.mark.slow
def test_hop_to_next_server(livebot):
    port, server, bot, bot_t, channel, nick = livebot
    bot.irc.servers = [["localhost", bot.irc.servers[0][1] + 1], bot.irc.servers[0]]  # bad port, con refused on 1st srv
    bot_t.start()
    assert nick in wait_until_joined(server, channel, nick)


@pytest.mark.slow
def test_quit_reconnect(livebot):
    port, server, bot, bot_t, channel, nick = livebot
    bot.irc.reconnect_delay = 0.1
    bot_t.start()
    wait_until_joined(server, channel, nick)
    bot.act_QUIT("quitting")
    wait_until_absent(server, channel, nick)
    assert nick in wait_until_joined(server, channel, nick)


def test_bs():
    IRCCore.fulltrace()
    IRCCore.trace()
