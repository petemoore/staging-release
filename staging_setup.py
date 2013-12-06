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


if __name__ == '__main__':

    log = logging.getLogger('staging release')
    # reading configuration
    config = Config()
    config_ini = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read_from(config_ini)
    tmp_dir = tempfile.mkdtemp()
    log.debug('tmp_dir: {0}'.format(tmp_dir))
    hg_cmd = ('clone', 'http://hg.mozilla.org/build/buildbot-configs', tmp_dir)
    for line in hg(hg_cmd, _iter=True):
        log.debug(line.strip())
    username = config.get('DEFAULT', 'username')
    basedir = config.get('master', 'basedir')
    http_port = config.get('master', 'http_port')
    ssh_port = config.get('master', 'ssh_port')
    pb_port = config.get('master', 'pb_port')
    role = config.get('master', 'role')
    virtualenv = config.get('master', 'virtualenv')

    if os.path.exists(basedir):
        log.error('{0} already exists. Terminating'.format(basedir))
        sys.exit(1)

    # creating basedir
    os.makedirs(basedir)

    # make
    make_cmd = ['-f', 'Makefile.setup']
    make_cmd += ['USE_DEV_MASTER=1']
    make_cmd += ['MASTER_NAME={0}'.format(username)]
    make_cmd += ['BASEDIR={0}'.format(basedir)]
    make_cmd += ['PYTHON=python2.6']
    make_cmd += ['VIRTUALENV=virtualenv-2.6']
    make_cmd += ['BUILDBOTCUSTOM_BRANCH=default']
    make_cmd += ['BUILDBOTCONFIGS_BRANCH=default']
    make_cmd += ['USER={0}'.format(username)]
    make_cmd += ['HTTP_PORT={0}'.format(http_port)]
    make_cmd += ['PB_PORT={0}'.format(pb_port)]
    make_cmd += ['SSH_PORT={0}'.format(ssh_port)]
    make_cmd += ['ROLE={0}'.format(role)]
    make_cmd += [virtualenv, 'deps', 'install-buildbot']
    make_cmd += ['master', 'master-makefile']
    make_cwd = os.path.join(tmp_dir)
    for line in ls(make_cwd, _iter=True):
        log.debug(line.strip())

    for line in make(make_cmd, _cwd=make_cwd, _iter=True):
        log.debug(line.strip())
    shutil.rmtree(tmp_dir)
