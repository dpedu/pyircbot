import pytest
import os
import hashlib
from time import sleep
from pyircbot.modules.DCC import int2ip
from tests.lib import *  # NOQA - fixtures


@pytest.fixture
def dccbot(fakebot):
    """
    Provide a bot loaded with the DCC module
    """
    fakebot.botconfig["module_configs"]["DCC"] = {
        "port_range": [40690, 40990],
        "public_addr": "127.0.0.1",
        "bind_host": "127.0.0.1"
    }
    fakebot.loadmodule("DCC")
    return fakebot


def test_offerrecv(dccbot, tmpdir):
    # allocate a temp file
    flen = 1024 * 51
    tmpfpath = os.path.join(tmpdir.dirname, "hello.bin")
    with open(tmpfpath, 'wb') as fout:
        fout.write(os.urandom(flen))
    # hash the tmpfile for later comparison
    m = hashlib.sha256()
    with open(tmpfpath, "rb") as ftmp:
        m.update(ftmp.read())
    srchash = m.hexdigest()
    # offer th file over DCC
    ip, port, reported_len, offer = dccbot.moduleInstances['DCC'].offer(tmpfpath)
    reported_len = int(reported_len)
    assert reported_len == flen, "offer reported wrong file length!"
    ip = int2ip(ip)
    while not offer.bound:
        sleep(0.001)
    # receive the file over DCC
    print("connecting to {}:{}".format(ip, port))
    recver = dccbot.moduleInstances['DCC'].recieve(ip, port, reported_len)
    data = b''
    d = hashlib.sha256()
    for chunk in iter(recver):
        data += chunk
        d.update(chunk)
    # verify hashes and lengths
    assert len(data) == flen, "file not completely transferred"
    assert d.hexdigest() == srchash, "file was mangled in transfer"
