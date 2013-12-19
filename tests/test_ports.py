import socket
from lib.ports import in_use
from lib.ports import used_in_range
from lib.ports import available_in_range


def test_in_use():
    sock = socket.socket()
    sock.bind(('', 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    assert in_use(port) is True
    sock.close()
    assert in_use(port) is False


def test_used_in_range():
    sock = socket.socket()
    sock.bind(('', 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    used = used_in_range(port, port + 1)
    sock.close()
    assert port in used


def test_available_in_range():
    sock = socket.socket()
    sock.bind(('', 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    avail = available_in_range(port, port + 1)
    sock.close()
    assert port not in avail
