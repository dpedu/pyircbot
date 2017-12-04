import os
import pytest
from pyircbot import jsonrpc
from threading import Thread
from random import randint
from socket import SHUT_RDWR
from time import sleep


# Sample server methods

def sample(value):
    return value


class _sample(object):
    def sample(self, value):
        return value


def client(port, v=2):
    return jsonrpc.ServerProxy((jsonrpc.JsonRpc20 if v == 2 else jsonrpc.JsonRpc10)(),
                               jsonrpc.TransportTcpIp(addr=("127.0.0.1", port), timeout=2.0))


# Fixures for each server version provide a (server_instance, port) tuple.
# Each have the method "sample", which returns the value passed
# Each have a class instance registered as "obj", which the method "sample" as well

@pytest.fixture
def j1testserver():
    port = randint(40000, 60000)
    server = jsonrpc.Server(jsonrpc.JsonRpc10(),
                            jsonrpc.TransportTcpIp(addr=("127.0.0.1", port)))
    server.register_function(sample)
    server.register_instance(_sample(), name="obj")
    Thread(target=server.serve, daemon=True).start()
    sleep(0.1)  # Give the serve() time to set up the serversocket
    yield (server, port)
    server._Server__transport.s.shutdown(SHUT_RDWR)


@pytest.fixture
def j2testserver():
    port = randint(40000, 60000)
    server = jsonrpc.Server(jsonrpc.JsonRpc20(),
                            jsonrpc.TransportTcpIp(addr=("127.0.0.1", port)))
    server.register_function(sample)
    server.register_instance(_sample(), name="obj")
    Thread(target=server.serve, daemon=True).start()
    sleep(0.1)  # Give the serve() time to set up the serversocket
    yield (server, port)
    server._Server__transport.s.shutdown(SHUT_RDWR)


# Basic functionality
def test_1_basic(j1testserver):
    str(jsonrpc.RPCFault(-32700, "foo", "bar"))
    server, port = j1testserver
    str(client(port, v=1))
    ret = client(port, v=1).sample("foobar")
    assert ret == "foobar"


def test_2_basic(j2testserver):
    server, port = j2testserver
    str(client(port))
    ret = client(port).sample("foobar")
    assert ret == "foobar"


def test_1_instance(j1testserver):
    server, port = j1testserver
    ret = client(port, v=1).obj.sample("foobar")
    assert ret == "foobar"


def test_2_instance(j2testserver):
    server, port = j2testserver
    ret = client(port).obj.sample("foobar")
    assert ret == "foobar"


# Missing methods raise clean error
def test_1_notfound(j1testserver):
    server, port = j1testserver
    with pytest.raises(jsonrpc.RPCMethodNotFound):
        client(port, v=1).idontexist("f")
    with pytest.raises(jsonrpc.RPCMethodNotFound):
        client(port, v=1).neither.idontexist("f")


def test_2_notfound(j2testserver):
    server, port = j2testserver
    with pytest.raises(jsonrpc.RPCMethodNotFound):
        client(port).idontexist("f")
    with pytest.raises(jsonrpc.RPCMethodNotFound):
        client(port).neither.idontexist("f")


# Underscore methods are blocked
def test_1_underscore():
    with pytest.raises(AttributeError):
        client(-1)._notallowed()


def test_2_underscore():
    with pytest.raises(AttributeError):
        client(-1)._notallowed()


# Response parsing hardness
def _test_1_protocol_parse_base(method):
    with pytest.raises(jsonrpc.RPCParseError):  # Not json
        method("")
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # Not a dict
        method("[]")
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # Missing 'id'
        method("{}")
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # not 3 fields
        method('{"id": 0, "baz": 0}')


def _test_2_protocol_parse_base(method):
    with pytest.raises(jsonrpc.RPCParseError):  # Not json
        method("")
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # Not a dict
        method("[]")
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # missing jsonrpc
        method('{}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # jsonrpc must be str
        method('{"jsonrpc": 1}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # jsonrpc must be "2.0"
        method('{"jsonrpc": "2.1"}')


def test_1_invalid_response():
    j = jsonrpc.JsonRpc10()
    _test_1_protocol_parse_base(j.loads_response)
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # can't have result and error
        j.loads_response('{"id": 0, "result": 1, "error": 0}')


def test_2_invalid_response():
    j = jsonrpc.JsonRpc20()
    _test_2_protocol_parse_base(j.loads_response)
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # Missing 'id'
        j.loads_response('{"jsonrpc": "2.0"}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # not 4 fields
        j.loads_response('{"id": 0, "jsonrpc": "2.0", "bar": 1}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # can't have result and error
        j.loads_response('{"id": 0, "jsonrpc": "2.0", "result": 1, "error": 0}')


# Request parsing hardness
def test_1_invalid_request():
    j = jsonrpc.JsonRpc10()
    _test_1_protocol_parse_base(j.loads_request)

    with pytest.raises(jsonrpc.RPCInvalidRPC):  # missing method
        j.loads_request('{"id": 0}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # method must be str
        j.loads_request('{"id": 0, "method": -1}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # params is bad type
        j.loads_request('{"id": 0, "method": "foo", "params": -1}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # wrong number of fields
        j.loads_request('{"ba": 0, "method": "foo", "asdf": 1, "foobar": 2}')
    j.loads_request('{"id": 0, "method": "foo", "params": []}')
    j.loads_request('{"method": "foo", "params": []}')


# Request parsing hardness
def test_2_invalid_request():
    j = jsonrpc.JsonRpc20()
    _test_2_protocol_parse_base(j.loads_request)

    with pytest.raises(jsonrpc.RPCInvalidRPC):  # missing method
        j.loads_request('{"id": 0, "jsonrpc": "2.0"}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # method must be str
        j.loads_request('{"id": 0, "jsonrpc": "2.0", "method": 1}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # params is bad type
        j.loads_request('{"id": 0, "jsonrpc": "2.0", "method": "foo", "params": -1}')
    with pytest.raises(jsonrpc.RPCInvalidRPC):  # wrong number of fields
        j.loads_request('{"id": 0, "jsonrpc": "2.0", "method": "foo", "asdf": 1, "foobar": 2}')
    j.loads_request('{"id": 0, "jsonrpc": "2.0", "method": "foo", "params": []}')
    j.loads_request('{"jsonrpc": "2.0", "method": "foo", "params": []}')


def test_1_dumps_reqest():
    j = jsonrpc.JsonRpc20()
    with pytest.raises(TypeError):
        j.dumps_request(-1)
    with pytest.raises(TypeError):
        j.dumps_request("foo", params=-1)
    j.dumps_request("foo")


def test_2_dumps_reqest():
    j = jsonrpc.JsonRpc20()
    with pytest.raises(TypeError):
        j.dumps_request(-1)
    with pytest.raises(TypeError):
        j.dumps_request("foo", params=-1)
    j.dumps_request("foo", params=[])
    j.dumps_request("foo")


# Misc stuff
def test_logging(tmpdir):
    msg = "test log message"
    jsonrpc.log_dummy(msg)
    jsonrpc.log_stdout(msg)
    logpath = os.path.join(tmpdir, "test.log")
    logger = jsonrpc.log_file(logpath)
    logger(msg)
    assert os.path.exists(logpath)

    logpath = os.path.join(tmpdir, "test2.log")
    logger2 = jsonrpc.log_filedate(os.path.join(tmpdir, "test2.log"))
    logger2(msg)
    assert os.path.exists(logpath)
