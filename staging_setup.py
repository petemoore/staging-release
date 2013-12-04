#!/usr/bin/env python

#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master

import socket
import subprocess
import logging


def run_command(cmd, env, cwd):
    proc = Subprocess.Popen(cmd, env=env, cwd=cwd)
    proc.wait()
    
def ports_in_use(from_port, to_port):
    is_open = False
    ports_in_use = set()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in xrange(from_port, to_port + 1):
        print port
        if sock.connect_ex(('127.0.0.1', port)) == 0:
            ports_in_use.add(port)
    sock.close()
    return ports_in_use

if __name__ == '__main__':
    print ports_in_use(5000, 5200)
