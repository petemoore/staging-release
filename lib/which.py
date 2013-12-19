# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python/
import os

"""
.. module:: which
    :platform: Unix, Windows
    :synopsis: a python implementation of which command
.. moduleauthor:: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python/
"""


def which(program):
    """a python implementation of 'which' command.
       It checks if program is in your PATH and returns the full path of it.
       If program is not in your PATH it returns None
    :param program: program to find
    :type program: str.
    :returns: str -- path if found, None otherwise
    """
    def is_executable(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_executable(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_executable(exe_file):
                return exe_file

    return None
