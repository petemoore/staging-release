"""creates and configures ship it"""
import os
from lib.venv import Virtualenv, VirtualenvError
from sh import git
import stat

from lib.logger import logger
log = logger(__name__)


class ShipitError(Exception):
    """Generic Shipit error"""
    pass


class Shipit(object):
    """creates a shipit instance"""
    def __init__(self, configuration):
        self.repository = configuration.get('shipit', 'repository')
        self.basedir = configuration.get('shipit', 'basedir')
        self.requirements = configuration.get_list('shipit', 'requirements')
        self.configuration = configuration
        self.activate_path = None
        self.python_path = None

    def install(self):
        """installs buildbot master"""
        log.info('installing ship it')
        self._clone(self.basedir)
        self.create_virtualenv()
        self._create_startup_file()

    def create_virtualenv(self):
        """creates a virtualenv for ship it
           and install all the required packages
        """
        venv = Virtualenv(self.configuration)
        try:
            venv.create(self.basedir)
            req = self.requirements
            if len(req) == 1:
                req = req[0]
            venv.install_dependencies(req)
        except VirtualenvError as error:
            msg = 'cannot create virtualenv: {0}'.format(error.message)
            log.error(msg)
            raise ShipitError(msg)

        self.activate_path = venv._activate_path()
        self.python_path = venv._python_path()

    def _clone(self, target_dir):
        """clones buildbot-configs into target_dir"""
        log.info('cloning {0}'.format(self.repository))
        git_cmd = ('clone', self.repository, target_dir)
        for line in git(git_cmd, _iter=True):
            log.debug(line.strip())

    def _create_startup_file(self):
        startup = self.configuration.get('shipit', 'startup')
        startup_path = self.configuration.get('shipit', 'startup_path')
        log.info('writing ship it startup file')
        conf = self.configuration
        username = conf.get('shipit', 'user')
        password = conf.get('shipit', 'password')
        with open(startup_path, 'w') as startup_script:
            startup_script.write('#!/bin/bash\n\n')
            startup_script.write('cd "$(dirname $0)"\n')
            startup_script.write('echo "username: {0}"\n'.format(username))
            startup_script.write('echo "password: {0}"\n'.format(password))
            startup_script.write('source {0}\n'.format(self.activate_path))
            startup_script.write("{0} {1}\n".format(self.python_path, startup))

        # log the new file
        log.debug('shipit startup file')
        with open(startup_path, 'r') as startup_script:
            for line in startup_script:
                log.debug(line.strip())

        # make it executable (the hard way)
        st = os.stat(startup_path)
        os.chmod(startup_path, st.st_mode | stat.S_IEXEC)

    def start(self):
        """starts a ship it instance"""
        pass

    def stop(self):
        """stops a ship it instance"""
        pass
