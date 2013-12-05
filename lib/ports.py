"""
this module provides a mechanism to check if a port or a range of ports
are already in use or it's free
"""
import socket


def in_use(port):
    """ checks if given port is in use."""
    is_open = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sock.connect_ex(('127.0.0.1', port)) == 0:
        is_open = True
    sock.close()
    return is_open


def used_in_range(from_port, to_port):
    """returns a set containing ports in use in a given range"""
    # this function uses the same socket instead of allocating
    # a socket for each port
    in_use = set()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in xrange(from_port, to_port):
        if sock.connect_ex(('127.0.0.1', port)) == 0:
            in_use.add(port)
    sock.close()
    return in_use


def available_in_range(from_port, to_port):
    """returns a list of available ports in a given range"""
    are_free = set()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in xrange(from_port, to_port):
        if not sock.connect_ex(('127.0.0.1', port)) == 0:
            are_free.add(port)
    return are_free
