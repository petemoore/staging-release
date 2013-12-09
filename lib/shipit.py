"""creates and configures ship it"""
import os
from lib.venv import Virtualenv, VirtualenvError
from sh import git
import lib.logger
import logging

log = logging.getLogger(__name__)


class ShipitError(Exception):
    """Generic Shipit error"""
    pass


class Shipit(object):
    """creates a shipit instance"""
    def __init__(self, configuration):
        self.repository = configuration.get('shipit', 'repository')
        self.username = configuration.get('shipit', 'username')
        self.password = configuration.get('shipit', 'password')
        self.basedir = configuration.get('shipit', 'basedir')
        req = configuration.get('shipit', 'requirements')
        self.requirements = os.path.join(self.basedir, req)
        self.configuration = configuration

    def install(self):
        """installs buildbot master"""
        self._clone(self.basedir)
        self.create_virtualenv()

    def create_virtualenv(self):
        """creates a virtualenv for ship it
           and install all the required packages
        """
        venv = Virtualenv(self.configuration)
        try:
            venv.create(self.basedir, self.requirements)
        except VirtualenvError as error:
            msg = 'cannot create virtualenv: {0}'.format(error.message)
            log.error(msg)
            raise ShipitError(msg)

    def _clone(self, target_dir):
        """clones buildbot-configs into target_dir"""
        log.info('cloning {0}'.format(self.repository))
        git_cmd = ('clone', self.repository, target_dir)
        for line in git(git_cmd, _iter=True):
            log.debug(line.strip())

    def _create_startup_file(self):
        pass

    def start(self):
        """starts a ship it instance"""
        pass

    def stop(self):
        """stops a ship it instance"""
        pass
