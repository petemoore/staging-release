"""
this module manages the configuration
"""
import os
import pwd
import random
import string
import logging
import lib.ports as ports
import lib.logger
from configparser import ConfigParser, ExtendedInterpolation

log = logging.getLogger(__name__)


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


class Config(ConfigParser):
    """this class manages the configuration"""
    def __init__(self):
        ConfigParser.__init__(self, interpolation=ExtendedInterpolation())

    def read_from(self, filenames):
        """reads the configuration from a file or a list of files
           and then generates some runtime specific values
           as (ports, passwords,..)"""
        self.read(filenames)
        self._set_runtime_values()

    def _set_runtime_values(self):
        """this method collects all the values that should be
            determined at runtime"""
        self._set_username()
        self._set_shipit_password()
        self._set_shipit_port()
        self._set_master_ports()

    def _set_username(self):
        # username cannot be hard coded in config.ini
        # it must be determined at run time
        # since username is a common option, let's have
        # it in the DEFAULT section so it will be available
        # in every section -- what about switching to python3 for
        # better interpolation?
        """sets the username
           assumption: your LDAP username is the same as your account
           on devmaster-01
        """
        username = get_username()
        log.debug('username: {0}'.format(username))
        self.set('DEFAULT', 'username', username)

    def _set_shipit_password(self):
        """generates a random password for shipit"""
        # so there is no need to store a password in config.ini
        password = generate_random_password()
        log.debug('shipit password: {0}'.format(password))
        self.set('shipit', 'password', password)

    def _set_shipit_port(self):
        """finds an empty port for shipit"""
        shipit_base_port = int(self.get('shipit', 'shipit_port_range'))
        available_ports = ports.available_in_range(shipit_base_port,
                                                   shipit_base_port + 1000)
        shipit_port = str(available_ports.pop())
        log.debug('shipit port: {0}'.format(shipit_base_port))
        self.set('shipit', 'port', shipit_port)

    def _set_master_ports(self):
        """finds three random ports for master (pb, ssh and http)"""
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
                log.debug('master ports:')
                log.debug('http: {0}'.format(http_port))
                log.debug('ssh: {0}'.format(ssh_port))
                log.debug('pb: {0}'.format(pb_port))
                self.set('master', 'ssh_port', str(ssh_port))
                self.set('master', 'pb_port', str(pb_port))
                self.set('master', 'http_port', str(http_port))
                return

        # no available ports!
        # giving up
        msg = "no available ports for your staging master. Giving up"
        raise ConfigError(msg)

    def __str__(self):
        msg = ""
        for section in self.sections():
            msg = "{0}[{1}]\n".format(msg, section)
            for option in self.options(section):
                msg = "{0}{1}={2}\n".format(msg, option,
                                            self.get(section, option))
        return msg


def duplicate(configuration):
    conf = Config()
    print "******"
    print conf
    print "******"

    conf.read_dict(configuration)
    return conf

