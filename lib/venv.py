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
        self.binaries = configuration.get_list('virtualenv', 'binaries')
        self.virtualenv = configuration.get('virtualenv', 'virtualenv')

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

    def _get_path(self, name):
        conf = self.configuration
        path = conf.get('virtualenv', name)
        if os.path.exists(self.basedir):
            path = os.path.join(self.basedir, path)
        return path

    def _python_path(self):
        return self._get_path('python_path')

    def _activate_path(self):
        return self._get_path('activate_path')

    def _pip_path(self):
        return self._get_path('pip')

    def create(self, dst_dir, extra_args=None):
        """creates a virtualenv in dst_dir and installs
           the required packages from requirements_file
        """
        if not self._executable():
            raise VirtualenvError('virtualenv is not installed')
        if extra_args is None:
            extra_args = []
        self.basedir = dst_dir

        cmd = [self._executable()] + extra_args + [self.basedir]
        log.info('creating virtualenv')
        venv = subprocess.Popen(cmd, cwd=self.basedir, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        while True:
            log.debug(venv.stdout.readline().strip())
            if venv.poll() is not None:
                break

    def setup_py(self, setup_py_path, options):
        """runs setup.py in the current virtualenv, using options"""
        log.info('running: {0} {1}'.format(setup_py_path, ' '.join(options)))
        cmd = [self._python_path(), setup_py_path] + options
        # http://stackoverflow.com/questions/14865990/python-module-wont-install
        cwd = os.path.dirname(setup_py_path)
        log.debug('executing: {0} in {1}'.format(' '.join(cmd), cwd))
        setup = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        while True:
            log.debug(setup.stdout.readline().strip())
            if setup.poll() is not None:
                break

    def _install(self, install_cmd):
        cmd = [self._pip_path()] + install_cmd
        log.debug('running {0} cwd={1}'.format(' '.join(cmd), self.basedir))
        pip = subprocess.Popen(cmd, cwd=self.basedir, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        while True:
            log.debug(pip.stdout.readline().strip())
            if pip.poll() is not None:
                break

    def install_dependency(self, dependency):
        if os.path.exists(dependency):
            # it's a file
            log.debug('installing dependencies from {0}'.format(dependency))
            self._install(['install', '-r', dependency])
        else:
            log.debug('{0} is not a file'.format(dependency))
            log.debug('installing dependency {0}'.format(dependency))
            self._install(['install', dependency])

    def install_dependencies(self, dependencies):
        log.info('installing virtualenv dependencies')
        if not isinstance(dependencies, list):
            dependencies = [dependencies]
        for dependency in dependencies:
            self.install_dependency(dependency)
