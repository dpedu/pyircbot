"""
.. module:: DCC
    :synopsis: Module providing support for IRC's dcc protocol

.. moduleauthor:: Dave Pedu <dave@davepedu.com>

"""

import os
from pyircbot.modulebase import ModuleBase
import socket
from threading import Thread
from random import randint
from time import sleep


BUFFSIZE = 8192


class TransferFailedException(Exception):
    pass


def ip2int(ipstr):
    """
    Convert an ip address string to an integer
    """
    num = 0
    for octet in ipstr.split("."):
        num = num << 8 | int(octet)
    return num


def int2ip(num):
    """
    Convert an integer to an ip address string
    """
    octs = []
    for octet in range(0, 4):
        octs.append(str((num & (255 << (8 * octet))) >> (8 * octet)))
    return ".".join(octs[::-1])


class DCC(ModuleBase):
    def __init__(self, bot, name):
        super().__init__(bot, name)
        self.services = ["dcc"]
        self.is_kill = False
        self.transfers = []

    def offer(self, file_path, port=None):
        """
        Offer a file to another user.
        - check file size
        - start listener socket thread on some port
        - info about the file: tuple of (ip, port, size)
        """
        port_range = self.config.get("port_range", [40000, 60000])  # TODO it would be better to let the system assign
        port = randint(*port_range)
        bind_addr = self.config.get("bind_host", "0.0.0.0")
        advertise_addr = self.config.get("public_addr", bind_addr)
        flen = os.path.getsize(file_path)
        offer = OfferThread(self, file_path, bind_addr, port)  # offers are considered ephemeral. even if this module is
        # unloaded, initiated transfers may continue. They will not block python from exiting (at which time they *will*
        # be terminated).
        offer.start()
        return (ip2int(advertise_addr), port, flen, offer)

    def recieve(self, host, port, length):
        """
        Receive a file another user has offered. Returns a generator that yields data chunks.
        """
        return RecieveGenerator(host, port, length)


class RecieveGenerator(object):
    def __init__(self, host, port, length):
        self.host = host
        self.port = port
        self.length = length

    def __iter__(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        total = 0
        try:
            while True:
                if total == self.length:
                    break
                chunk = self.sock.recv(BUFFSIZE)
                total += len(chunk)
                if not chunk:
                    break
                yield chunk
                if total >= self.length:
                    break
            print("total", total, "expected", self.length)
            if total != self.length:
                raise TransferFailedException("Transfer failed: expected {} bytes but got {}".format(self.length, total))
            raise StopIteration()
        finally:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()


class OfferThread(Thread):
    def __init__(self, master, path, bind_addr, port, timeout=30):
        """
        DCC file transfer offer listener
        :param master: reference to the parent module
        :param path: file path to be opened and transferred
        :param bind_addr: address str to bind the listener socket to
        :param port: port number int to listen on
        :param timeout: number of seconds to give up after
        """
        super().__init__()
        self.master = master
        self.path = path
        self.bind = bind_addr
        self.port = port
        self.timeout = timeout
        self.listener = None
        self.daemon = True
        self.bound = False
        Thread(target=self.abort, daemon=True).start()

    def run(self):
        """
        Open a server socket that accepts a single connections. When the first client connects, send the contents of the
        offered file.
        """
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.listener.bind((self.bind, self.port))
            self.listener.listen(1)
            self.bound = True
            (clientsocket, address) = self.listener.accept()
            try:
                self.send_file(clientsocket)
            finally:
                clientsocket.shutdown(socket.SHUT_RDWR)
                clientsocket.close()
        finally:
            self.listener.shutdown(socket.SHUT_RDWR)
            self.listener.close()

    def abort(self):
        """
        Expire the offer after a timeout.
        """
        sleep(self.timeout)
        self.stopoffer()

    def send_file(self, socket):
        """
        Send the contents of the offered file to the passed socket
        :param socket: socket object ready for sending
        :type socket: socket.socket
        """
        with open(self.path, 'rb') as f:
            while not self.master.is_kill:
                chunk = f.read(BUFFSIZE)
                if not chunk:
                    break
                socket.send(chunk)

    def stopoffer(self):
        """
        Prematurely shut down & cleanup the offer socket
        """
        try:
            self.listener.shutdown(socket.SHUT_RDWR)
            self.listener.close()
        except Exception:   # should only error if already cleaned up
            pass
