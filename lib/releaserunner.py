"""creates and configures release runner"""
import os
import sh
import lib.logger
import logging
import stat
from lib.config import Config
from lib.venv import Virtualenv, VirtualenvError

log = logging.getLogger(__name__)


class ReleaseRunnerError(Exception):
    """Generic ReleaseRunner error"""
    pass


class ReleaseRunner(object):
    """creates a release runner instance"""
    def __init__(self, configuration):
        self.basedir = configuration.get('release_runner', 'basedir')
        self.username = configuration.get('release_runner', 'username')
        self.password = configuration.get('shipit', 'password')
        self.repository = configuration.get('release_runner', 'repository')
        self.tracking_bug = configuration.get('release_runner', 'tracking_bug')
        self.requirements = configuration.get('release_runner', 'requirements')
        self.requirements = self.requirements.split(',')
        self.configuration = configuration
        self.activate_path = None
        self.python_path = None

    def install(self):
        """installs buildbot master"""
        log.info('installing release runner')
        self._clone(self.basedir)
        self.create_virtualenv()
        self._create_startup_file()

    def _clone(self, target_dir):
        """clones buildbot-configs into target_dir"""
        log.info('cloning {0}'.format(self.repository))
        hg_cmd = ('clone', self.repository, target_dir)
        for line in sh.hg(hg_cmd, _iter=True):
            log.debug(line.strip())

    def _create_startup_file(self):
        startup = self.configuration.get('release_runner', 'startup')
        startup_path = self.configuration.get('release_runner', 'startup_path')
        log.info('writing release runner startup file')
        with open(startup_path, 'w') as startup_script:
            startup_script.write('#!/bin/bash\n\n')
            startup_script.write('cd "$(dirname $0)"\n')
            startup_script.write('source {0}\n'.format(self.activate_path))
            startup_script.write("{0} {1}\n".format(self.python_path, startup))

        # log the new file
        with open(startup_path, 'r') as startup_script:
            log.debug(startup_script)

        # make it executable (the hard way)
        st = os.stat(startup_path)
        os.chmod(startup_path, st.st_mode | stat.S_IEXEC)

    def create_ini_file(self):
        src_ini_file = self.configuration.get('release_runner', 'src_ini_file')
        dst_ini_file = self.configuration.get('release_runner', 'dst_ini_file')
        pb_port = self.configuration.get('master', 'pb_port')
        # we need a new configuration for our new ini file
        # so we can inject values form the our current config (port, user, ...)
        conf = Config()
        conf.set('DEFAULT', 'pb_port', pb_port)
        conf.set('DEFAULT', 'username', self.username)
        conf.set('DEFAULT', 'password', self.password)
        conf.set('DEFAULT', 'tracking_bug', self.tracking_bug)
        # read src_ini_file, write it into the dst_ini_file
        # and log the new content
        conf.read_file(src_ini_file)
        with open(dst_ini_file, 'w') as dst:
            conf.write(dst)

    def create_virtualenv(self):
        """creates a virtualenv for release runner
           and install all the required packages
        """
        venv = Virtualenv(self.configuration)
        self.activate_path = venv.activate_path
        self.python_path = venv.python_path
        try:
            venv.create(self.basedir)
            venv.install_requirements(self.requirements)
        except VirtualenvError as error:
            msg = 'cannot create virtualenv: {0}'.format(error.message)
            log.error(msg)
            raise ReleaseRunnerError(msg)

    def start(self):
        """starts a release runner instance"""
        # it's a blocking operation.
        log.info('starting release runner')
        startup_path = self.configuration.get('release_runner', 'startup_path')
        sh(startup_path)

    def stop(self):
        """stops a release runner instance"""
        pass
