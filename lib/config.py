"""
this module manages the configuration
"""
import ConfigParser
import os
import pwd


def get_username():
    """
    a replacement for whoami command
    """
    return pwd.getpwuid(os.getuid())[0]


class Config(ConfigParser.SafeConfigParser):
    """
    this class manages the configuration. It also populates the configuration
    with somevalues (e.g. username) that can be determined only at run time.

    """
    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        # username cannot be hard coded in config.ini
        # it must be determined at run time
        # since username is a common option, let's have
        # it in the DEFAULT section so it will be available
        # in every section -- what about switching to python3 for
        # better interpolation?
        self.set('DEFAULT', 'username', get_username())
