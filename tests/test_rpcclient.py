from tests.lib import *  # NOQA - fixtures

from unittest.mock import MagicMock, call
from pyircbot.rpc import BotRPC
from pyircbot.rpcclient import connect
from random import randint
from time import sleep


def test_rpc(monkeypatch):
    port = randint(40000, 65000)
    m = MagicMock()
    m.botconfig = {"bot": {"rpcbind": "127.0.0.1", "rpcport": port}}
    server = BotRPC(m)
    sleep(0.05)

    calltrack = MagicMock()

    def fake(*args):
        calltrack(*args)
        return args

    for k, v in server.server.funcs.items():
        server.server.funcs[k] = fake

    methods = [["importModule", "foo"],
               ["deportModule", "foo"],
               ["loadModule", "foo"],
               ["unloadModule", "foo"],
               ["reloadModule", "foo"],
               ["redoModule", "foo"],
               ["getLoadedModules"],
               ["pluginCommand", "foo", "foo", "foo"],
               ["setPluginVar", "foo", "foo"],
               ["getPluginVar", "foo", "foo", "foo"],
               ["eval", "foo"],
               ["exec", "foo"],
               ["quit", "foo"]]

    client = connect("127.0.0.1", port)

    for test in methods:
        method = test[0]
        args = test[1:]
        server.server.funcs[method] = fake
        print("Calling {} with: {}".format(method, args))
        getattr(client, method)(*args)
        calltrack.assert_called_once_with(*args)
        calltrack.reset_mock()


def test_rpc_internal(monkeypatch):
    port = randint(40000, 65000)
    m = MagicMock()
    m.botconfig = {"bot": {"rpcbind": "127.0.0.1", "rpcport": port}}
    server = BotRPC(m)

    methods = [["importModule", "foo"],
               ["deportModule", "foo"],
               ["loadModule", "foo"],
               ["unloadModule", "foo"],
               ["redoModule", "foo"],]

    for test in methods:
        method = test[0]
        args = test[1:]
        getattr(server, method)(*args)
        getattr(m, method.lower()).assert_called_once_with(*args)
        getattr(m, method.lower()).reset_mock()

    m.moduleInstances = {"Foo": None, "Bar": None}
    assert server.getLoadedModules() == ["Foo", "Bar"]

    m.reset_mock()

    server.reloadModule("Foo")
    m.unloadmodule.assert_called_once_with("Foo")
    m.loadmodule.assert_called_once_with("Foo")

    m.reset_mock()

    # ["pluginCommand", "foo", "foo", "foo"],
    # ["setPluginVar", "foo", "foo"],
    # ["getPluginVar", "foo", "foo", "foo"]
    # ["eval", "foo"],
    # ["exec", "foo"],
    # ["quit", "foo"]]
