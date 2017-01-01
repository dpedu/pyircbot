from sys import argv, exit
from pyircbot import jsonrpc


def connect(host, port):
    return jsonrpc.ServerProxy(jsonrpc.JsonRpc20(), jsonrpc.TransportTcpIp(addr=(host, port), timeout=60.0))


if __name__ == "__main__":
    if len(argv) is not 3:
        print("Expected ip and port arguments")
        exit(1)
    print("Connecting to pyircbot rpc on port %s:%s..." % (argv[1], argv[2]))
    rpc = connect(argv[1], int(argv[2]))
    print("Connected to rpc")
    print("Loaded modules: %s" % rpc.getLoadedModules())
