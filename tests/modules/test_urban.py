import pytest
from unittest.mock import MagicMock
from tests.lib import *  # NOQA - fixtures
import requests


@pytest.fixture
def urbanbot(fakebot):
    """
    Provide a bot loaded with the Seen module
    """
    fakebot.loadmodule("Urban")
    return fakebot


def test_seen(urbanbot, monkeypatch):
    def fakeget(url, params=None):
        r = MagicMock()
        r.json = lambda: {"list": [{"definition": "A process for testing things", "defid": 708924}]}
        return r
    monkeypatch.setattr(requests, 'get', fakeget)
    urbanbot.feed_line(".u test")
    urbanbot.act_PRIVMSG.assert_called_once_with('#test', "Urban definition: A process for testing things - http://urbanup.com/708924")
