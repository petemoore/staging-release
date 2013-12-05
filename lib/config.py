"""
this module manages the configuration
"""
import ConfigParser
import os
import pwd
import ports
import random
import string


def get_username():
    """
    a replacement for whoami command
    """
    return pwd.getpwuid(os.getuid())[0]


def generate_random_password(size=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for x in range(size))


class ConfigError(Exception):
    pass


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

    def shipit_password(self):
        self.set('shipit', 'password', generate_random_password())

    def master_ports(self):
        # right now:
        # http port is in range 8000-8999
        # ssh port == http_port - 1000
        # pb_port == http_poer + 1000
        http_base_port = int(self.get('master', 'http_port_range'))
        ssh_base_port = int(self.get('master', 'ssh_port_range'))
        pb_base_port = int(self.get('master', 'pb_port_range'))
        available_ports = ports.available_in_range(http_base_port,
                                                   http_base_port + 1000)

        for http_port in available_ports:
            # available_port is a set so http_port is a random available
            # port in range http_base_port, http_base_port + 1000
            # (set are unsorted collections)
            suffix = http_port - http_base_port
            # 8744 -> 744 (suffix)
            pb_port = pb_base_port + suffix
            ssh_port = ssh_base_port + suffix

            if not ports.in_use(pb_port) and not ports.in_use(ssh_port):
                # we have found 3 ports that fit into our algorithm!
                self.set('master', 'ssh_port', ssh_port)
                self.set('master', 'pb_port', pb_port)
                self.set('master', 'http_port', http_port)
                return

        # no available ports!
        # giving up
        msg = "no available ports for your staging master. Giving up"
        raise ConfigError(msg)
