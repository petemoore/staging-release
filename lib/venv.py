import os
from lib.which import which
import subprocess
import lib.logger
import logging

log = logging.getLogger(__name__)


class VirtualenvError(Exception):
    """Generic Virtualenv error"""


class Virtualenv(object):
    """Virtualenv class, creates a virtualenv"""
    def __init__(self, configuration):
        self.binaries = configuration.get('virtualenv', 'binaries').split(',')
        self.executable = None
        self.activate_path = configuration.get('virtualenv', 'activate_path')
        self.install_directory = configuration.get('virtualenv',
                                                   'install_directory')
        self.basedir = None
        self.configuration = configuration

    def _executable(self):
        """returns the virtualenv excutable"""
        if self.executable:
            return self.executable

        for binary in self.binaries:
            venv_exec = which(binary)
            if venv_exec:
                self.executable = venv_exec
                log.debug('virtualenv executable: {0}'.format(self.executable))
                return self.executable
        return self.executable

    def create(self, dst_dir, requirements_file):
        """creates a virtualenv in dst_dir and installs
           the required packages from requirements_file
        """
        if not self._executable():
            raise VirtualenvError('virtualenv is not installed')

        cwd = dst_dir
        cmd = (self._executable(), self.install_directory)
        log.info('creating virtualenv')
        venv = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE)
        while True:
            log.debug(venv.stdout.readline())
            if venv.poll() is not None:
                break

        self.basedir = dst_dir
        conf = self.configuration
        pip_path = conf.get('virtualenv', 'pip')
        pip_path = os.path.join(self.basedir, pip_path)
        cmd = (pip_path, 'install', '-r', requirements_file)
        log.info('installing required packages')
        pip = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE)
        while True:
            log.debug(pip.stdout.readline())
            if pip.poll() is not None:
                break
