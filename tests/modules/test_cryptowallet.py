import pytest
from tests.lib import *  # NOQA - fixtures
from unittest.mock import MagicMock, call
from tests.modules.test_nickuser import nickbot  # NOQA - fixture
from decimal import Decimal
from tests.lib import pm
import re
from pyircbot.modules.CryptoWalletRPC import BitcoinRPC


class ReallyFakeBitcoinRPC(BitcoinRPC):
    """
    Fake BitcoinRPC instance we mock into the test fakebot instances. We add the `balance` attribute which is used for
    keeping track of the fake account's balance
    """
    def __init__(self):
        super().__init__(logger=MagicMock(),
                         name="fake",
                         fullname="Fakecoin",
                         host="127.0.0.1",
                         port=12345,
                         username="foo",
                         password="bar",
                         precision=4,
                         reserve=5,
                         addr_re=re.compile("^FAKE[a-f0-9A-F]{12}$"))
        self.balance = Decimal("666.0067")

    def getAcctAddr(self, acct):
        return "FOOADDRESS"

    def getAcctBal(self, acct):
        return self.balance

    def send(self, fromAcct, toAddr, amount):
        return "txidFOOBAR"

    def move(self, fromAcct, toAcct, amount):
        return True


@pytest.fixture
def cryptobot(nickbot):
    """
    Provide a bot loaded with the CryptoWallet modules
.    """
    nickbot.botconfig["module_configs"]["CryptoWalletRPC"] = \
        {"types": {
            "FAKE": {
                "name": "Fakecoin",
                "host": "127.0.0.1",
                "username": "",
                "password": "",
                "port": 1234,
                "precision": 4,
                "reserve": 1.0,
                "link": "http://fakecoin.com/",
                "addrfmt": "^FAKE[a-f0-9A-F]{12}$"}}}

    nickbot.loadmodule("CryptoWalletRPC")
    nickbot.loadmodule("CryptoWallet")
    nickbot.moduleInstances['CryptoWalletRPC'].rpcservices['fake'] = ReallyFakeBitcoinRPC()
    return nickbot


def test_getbal_authed(cryptobot):
    cryptobot.feed_line(".getbal fake")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: Please .login to use this command.')


def test_setup(cryptobot, mynick="chatter"):
    pm(cryptobot, ".setpass foobar", nick=mynick)
    cryptobot.act_PRIVMSG.assert_called_once_with(mynick, '.setpass: You\'ve been logged in and your password has been set to "foobar".')
    cryptobot.act_PRIVMSG.reset_mock()
    # TODO shouldn't need .login here, the setpass does it
    pm(cryptobot, ".login foobar", nick=mynick)
    cryptobot.act_PRIVMSG.assert_called_once_with(mynick, '.login: You have been logged in from: cia.gov')
    cryptobot.act_PRIVMSG.reset_mock()


def test_getbal(cryptobot):
    test_setup(cryptobot)
    cryptobot.feed_line(".getbal fake")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: your balance is: 666.0067 FAKE')


def test_setaddr(cryptobot):
    # Must login
    cryptobot.feed_line(".setaddr fake FAKE123456789012")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: Please .login to use this command.')
    cryptobot.act_PRIVMSG.reset_mock()
    test_setup(cryptobot)
    # Invalid currency
    cryptobot.feed_line(".setaddr invalidcoin baz")
    cryptobot.act_PRIVMSG.assert_called_once_with(
        '#test',
        ".setaddr: 'invalidcoin' is not a supported currency. Supported currencies are: fake")
    cryptobot.act_PRIVMSG.reset_mock()
    # Invalid address
    cryptobot.feed_line(".setaddr fake baz")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', ".setaddr: 'baz' appears to be an invalid address.")
    cryptobot.act_PRIVMSG.reset_mock()
    # OK
    cryptobot.feed_line(".setaddr fake FAKE123456789012")
    cryptobot.act_PRIVMSG.assert_called_once_with(
        '#test',
        '.setaddr: Your address has been saved as: FAKE123456789012. Please verify that this is correct or your coins '
        'could be lost.')
    cryptobot.act_PRIVMSG.reset_mock()


def test_withdraw(cryptobot):
    test_setup(cryptobot)
    # Must set withdraw addr
    cryptobot.feed_line(".withdraw FAKE 400")
    cryptobot.act_PRIVMSG.assert_called_once_with(
        '#test',
        '.withdraw: You need to set a withdraw address before withdrawing. Try .setaddr')
    cryptobot.act_PRIVMSG.reset_mock()
    # Set withdraw addr
    cryptobot.feed_line(".setaddr FAKE FAKE123456789012")
    cryptobot.act_PRIVMSG.assert_called_once_with(
        '#test',
        '.setaddr: Your address has been saved as: FAKE123456789012. Please verify that this is correct or '
        'your coins could be lost.')
    cryptobot.act_PRIVMSG.reset_mock()
    # Withdraw with wrong decimal precision
    cryptobot.feed_line(".withdraw FAKE 400.00001")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', ".withdraw: FAKE has maximum 4 decimal places")
    cryptobot.act_PRIVMSG.reset_mock()
    # Withdraw too much
    cryptobot.feed_line(".withdraw FAKE 800")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', ".withdraw: You don't have enough FAKE to withdraw 800")
    cryptobot.act_PRIVMSG.reset_mock()
    # Withdraw below reserve
    cryptobot.feed_line(".withdraw FAKE 666")
    cryptobot.act_PRIVMSG.assert_has_calls(
        [call('#test', '.withdraw: Withdrawing that much would put you below the reserve (5 FAKE).'),
         call('#test', '.withdraw: The reserve is to cover network transaction fees. To recover it you must close your '
                       'account. (Talk to my owner)')])
    cryptobot.act_PRIVMSG.reset_mock()
    # Withdraw
    cryptobot.feed_line(".withdraw FAKE 400")
    cryptobot.act_PRIVMSG.assert_has_calls(
        [call('#test', 'chatter: .withdraw: 400 FAKE sent to FAKE123456789012.'),
         call('chatter', 'Withdrawal: (You)->FAKE123456789012: Transaction ID: txidFOOBAR')])
    cryptobot.act_PRIVMSG.reset_mock()


def test_send(cryptobot):
    test_setup(cryptobot)
    # Send too much
    cryptobot.feed_line(".send FAKE 800 FAKE123456789012")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', "chatter: .send: You don't have enough FAKE to send 800")
    cryptobot.act_PRIVMSG.reset_mock()
    # Send below reserve
    cryptobot.feed_line(".send FAKE 666 FAKE123456789012")
    cryptobot.act_PRIVMSG.assert_has_calls(
        [call('#test', '.send: Sending that much would put you below the reserve (5 FAKE).'),
         call('#test', '.send: The reserve is to cover network transaction fees. To recover it you must close your '
                       'account. (Talk to my owner)')])
    cryptobot.act_PRIVMSG.reset_mock()
    # Send with wrong decimal precision
    cryptobot.feed_line(".send FAKE 400.00001 FAKE123456789012")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', ".send: FAKE has maximum 4 decimal places")
    cryptobot.act_PRIVMSG.reset_mock()
    # Send
    cryptobot.feed_line(".send FAKE 400 FAKE123456789012")
    cryptobot.act_PRIVMSG.assert_has_calls(
        [call('#test', 'chatter: .send: 400 FAKE sent to FAKE123456789012.'),
         call('chatter', 'Send: (You)->FAKE123456789012: Transaction ID: txidFOOBAR')])
    cryptobot.act_PRIVMSG.reset_mock()


def test_getaddr(cryptobot):
    test_setup(cryptobot)
    cryptobot.feed_line(".getaddr FAKE")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: your FAKE deposit address is: FOOADDRESS')


def test_send_local(cryptobot):
    """
    Similar to test_send but we send to a mocked local account
    """
    test_setup(cryptobot)
    # Fails if chatter2 has password yet
    cryptobot.feed_line(".send FAKE 400 chatter2")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', "chatter: .send: chatter2 doesn't have a password set.")
    cryptobot.act_PRIVMSG.reset_mock()

    test_setup(cryptobot, mynick="chatter2")

    cryptobot.feed_line(".send FAKE 400 chatter2")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', 'chatter: .send: 400 FAKE sent to chatter2.')
    cryptobot.act_PRIVMSG.reset_mock()


def test_curinfo(cryptobot):
    cryptobot.feed_line(".curinfo")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test', ".curinfo: supported currencies: FAKE. Use "
                                                           "'.curinfo BTC' to see details.")
    cryptobot.act_PRIVMSG.reset_mock()
    cryptobot.feed_line(".curinfo fake")
    cryptobot.act_PRIVMSG.assert_called_once_with('#test',
                                                  ".curinfo: fake - Fakecoin. More info: http://fakecoin.com/")
