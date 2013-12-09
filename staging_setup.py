#!/usr/bin/env python

#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master
import os
import sys
import tempfile
import shutil
from lib.config import Config
from sh import hg
from sh import make
from sh import ls
import lib.logger
import logging


class MasterError(Exception):
    pass


class Master(object):
    def __init__(self, configuration):
        self.username = configuration.get('DEFAULT', 'username')
        self.basedir = configuration.get('master', 'basedir')
        self.http_port = configuration.get('master', 'http_port')
        self.ssh_port = configuration.get('master', 'ssh_port')
        self.pb_port = configuration.get('master', 'pb_port')
        self.role = configuration.get('master', 'role')
        self.virtualenv = configuration.get('master', 'virtualenv')

    def install(self):
        self._prepare_dirs()
        tmp_dir = tempfile.mkdtemp()
        log.info('tmp_dir: {0}'.format(tmp_dir))
        self._clone_builbot_configs(tmp_dir)
        self._make(tmp_dir)
        shutil.rmtree(tmp_dir)

    def _prepare_dirs(self):
        try:
            os.makedirs(self.basedir)
        except OSError as error:
            msg = 'Cannot create: {0} ({1})'.format(self.basedir, error)
            raise MasterError(msg)

    def _clone_builbot_configs(self, target_dir):
        log.info('cloning http://hg.mozilla.org/build/buildbot-configs')
        hg_cmd = ('clone', 'http://hg.mozilla.org/build/buildbot-configs', target_dir)
        for line in hg(hg_cmd, _iter=True):
            log.debug(line.strip())

    def _make(self, cwd):
        log.info('creating master in {0}'.format(self.basedir))
        make_cmd = ['-f', 'Makefile.setup']
        make_cmd += ['USE_DEV_MASTER=1']
        make_cmd += ['MASTER_NAME={0}'.format(self.username)]
        make_cmd += ['BASEDIR={0}'.format(self.basedir)]
        make_cmd += ['PYTHON=python2.6']
        make_cmd += ['VIRTUALENV=virtualenv-2.6']
        make_cmd += ['BUILDBOTCUSTOM_BRANCH=default']
        make_cmd += ['BUILDBOTCONFIGS_BRANCH=default']
        make_cmd += ['USER={0}'.format(self.username)]
        make_cmd += ['HTTP_PORT={0}'.format(self.http_port)]
        make_cmd += ['PB_PORT={0}'.format(self.pb_port)]
        make_cmd += ['SSH_PORT={0}'.format(self.ssh_port)]
        make_cmd += ['ROLE={0}'.format(self.role)]
        make_cmd += [self.virtualenv, 'deps', 'install-buildbot']
        make_cmd += ['master', 'master-makefile']

        for line in make(make_cmd, _cwd=cwd, _iter=True):
            log.debug(line.strip())


if __name__ == '__main__':

    log = logging.getLogger('staging release')
    # reading configuration
    config = Config()
    config_ini = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read_from(config_ini)
    master = Master(config)
    try:
        master.install()
    except MasterError as error:
        msg = 'master creation failed with the following error: {0}'.format(error)
        log.error(msg)



