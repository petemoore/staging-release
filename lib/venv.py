import os
from lib.which import which
import subprocess

from lib.logger import logger
log = logger(__name__)


class VirtualenvError(Exception):
    """Generic Virtualenv error"""


class Virtualenv(object):
    """Virtualenv class, creates a virtualenv"""
    def __init__(self, configuration):
        self.basedir = None
        self.executable = None
        self.configuration = configuration
        self.binaries = configuration.get('virtualenv', 'binaries').split(',')
        self.python_path = configuration.get('virtualenv', 'python_path')
        self.activate_path = configuration.get('virtualenv', 'activate_path')
        self.install_directory = configuration.get('virtualenv',
                                                   'install_directory')

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

    def create(self, dst_dir):
        """creates a virtualenv in dst_dir and installs
           the required packages from requirements_file
        """
        if not self._executable():
            raise VirtualenvError('virtualenv is not installed')

        self.basedir = dst_dir
        cmd = (self._executable(), self.install_directory)
        log.info('creating virtualenv')
        venv = subprocess.Popen(cmd, cwd=self.basedir, stdout=subprocess.PIPE)
        while True:
            log.debug(venv.stdout.readline().strip())
            if venv.poll() is not None:
                break

    def install_requirements(self, requirements):
        if isinstance(requirements, str):
            requirements = [requirements]
        conf = self.configuration
        pip_path = conf.get('virtualenv', 'pip')
        pip_path = os.path.join(self.basedir, pip_path)
        cmd = [pip_path, 'install'] + requirements
        log.info('installing required packages')
        pip = subprocess.Popen(cmd, cwd=self.basedir, stdout=subprocess.PIPE)
        while True:
            log.debug(pip.stdout.readline().strip())
            if pip.poll() is not None:
                break

    def install_requirements_from_file(self, requirements_file):
        conf = self.configuration
        pip_path = conf.get('virtualenv', 'pip')
        pip_path = os.path.join(self.basedir, pip_path)
        cmd = (pip_path, 'install', '-r', requirements_file)
        log.info('installing required packages')
        pip = subprocess.Popen(cmd, cwd=self.basedir, stdout=subprocess.PIPE)
        while True:
            log.debug(pip.stdout.readline().strip())
            if pip.poll() is not None:
                break