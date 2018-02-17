import pytest
import os
import hashlib
from time import sleep
from tests.lib import *  # NOQA - fixtures
from pyircbot.modules import DCC


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


def _make_test_tempfiles(length, basedir):
    tmpfpath = os.path.join(basedir.dirname, "hello.bin")
    with open(tmpfpath, 'wb') as fout:
        fout.write(os.urandom(length))
    # hash the tmpfile for later comparison
    m = hashlib.sha256()
    with open(tmpfpath, "rb") as ftmp:
        m.update(ftmp.read())
    srchash = m.hexdigest()
    return tmpfpath, srchash


@pytest.mark.slow
def test_offerrecv(dccbot, tmpdir):
    # allocate a temp file
    flen = 1024 * 51
    tmpfpath, srchash = _make_test_tempfiles(flen, tmpdir)
    # offer th file over DCC
    ip, port, reported_len, offer = dccbot.moduleInstances['DCC'].offer(tmpfpath)
    reported_len = int(reported_len)
    assert reported_len == flen, "offer reported wrong file length!"
    ip = DCC.int2ip(ip)
    while not offer.bound:
        sleep(0.001)
    # receive the file over DCC
    recver = dccbot.moduleInstances['DCC'].recieve(ip, port, reported_len)
    data = b''
    d = hashlib.sha256()
    for chunk in iter(recver):
        data += chunk
        d.update(chunk)
    # verify hashes and lengths
    assert len(data) == flen, "file not completely transferred"
    assert d.hexdigest() == srchash, "file was mangled in transfer"


@pytest.mark.slow
def test_tooshortfails(dccbot, tmpdir):
        # allocate a temp file
    flen = 1024 * 51
    tmpfpath, srchash = _make_test_tempfiles(flen, tmpdir)
    # offer th file over DCC
    ip, port, reported_len, offer = dccbot.moduleInstances['DCC'].offer(tmpfpath)
    reported_len = int(reported_len)
    assert reported_len == flen, "offer reported wrong file length!"
    ip = DCC.int2ip(ip)
    while not offer.bound:
        sleep(0.001)
    recver = dccbot.moduleInstances['DCC'].recieve(ip, port, reported_len + 1)  # the magic
    # fail to receive the file over DCC
    # with pytest.raises(TransferFailedException):
    try:
        for chunk in iter(recver):
            print(len(chunk))
    # except DCC.TransferFailedException as te:
    #    return
    except Exception as fe:
        assert fe.args == ('Transfer failed: expected 52225 bytes but got 52224',)
        return
    raise Exception("Did not raise")


@pytest.mark.slow
def test_toolongfails(dccbot, tmpdir):
        # allocate a temp file
    flen = 1024 * 51
    tmpfpath, srchash = _make_test_tempfiles(flen, tmpdir)
    # offer th file over DCC
    ip, port, reported_len, offer = dccbot.moduleInstances['DCC'].offer(tmpfpath)
    reported_len = int(reported_len)
    assert reported_len == flen, "offer reported wrong file length!"
    ip = DCC.int2ip(ip)
    while not offer.bound:
        sleep(0.001)
    recver = dccbot.moduleInstances['DCC'].recieve(ip, port, reported_len - 1)  # the magic
    # fail to receive the file over DCC
    # with pytest.raises(TransferFailedException):
    try:
        for chunk in iter(recver):
            print(len(chunk))
    # except DCC.TransferFailedException as te:
    #    return
    except Exception as fe:
        assert fe.args == ('Transfer failed: expected 52223 bytes but got 52224',)
        return
    raise Exception("Did not raise")
