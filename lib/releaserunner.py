"""creates and configures release runner"""
import os
import sh
import stat
from lib.venv import Virtualenv, VirtualenvError

from lib.logger import logger
log = logger(__name__)


class ReleaseRunnerError(Exception):
    """Generic ReleaseRunner error"""
    pass


class ReleaseRunner(object):
    """creates a release runner instance"""
    def __init__(self, configuration):
        self.basedir = configuration.get('release-runner', 'basedir')
        self.repository = configuration.get('release-runner', 'repository')
        self.requirements = configuration.get('release-runner', 'requirements')
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
        self.create_ini_file()

    def _clone(self, target_dir):
        """clones buildbot-configs into target_dir"""
        log.info('cloning {0}'.format(self.repository))
        hg_cmd = ('clone', self.repository, target_dir)
        for line in sh.hg(hg_cmd, _iter=True):
            log.debug(line.strip())

    def _create_startup_file(self):
        startup = self.configuration.get('release-runner', 'startup')
        startup_path = self.configuration.get('release-runner', 'startup_path')
        log.info('writing release runner startup file')
        with open(startup_path, 'w') as startup_script:
            startup_script.write('#!/bin/bash\n\n')
            startup_script.write('cd "$(dirname $0)"\n')
            startup_script.write('source {0}\n'.format(self.activate_path))
            startup_script.write("{0} {1}\n".format(self.python_path, startup))

        # log the new file
        with open(startup_path, 'r') as startup_script:
            log.debug(startup_script.read())

        # make it executable (the hard way)
        st = os.stat(startup_path)
        os.chmod(startup_path, st.st_mode | stat.S_IEXEC)

    def create_ini_file(self):
        conf = self.configuration
        dst_ini_file = conf.get('release-runner', 'dst_ini_file')
        # merged release_runner.ini with config.ini
        # no need for copy the configuration and importing values into
        # release runner... just save config.ini as relase_runner.ini
        conf.write_to(dst_ini_file)

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
        startup_path = self.configuration.get('release-runner', 'startup_path')
        sh(startup_path)

    def stop(self):
        """stops a release runner instance"""
        pass
