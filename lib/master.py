"""creates and cofigures a staging master"""
import os
import json
import tempfile
import shutil
from sh import hg
from sh import make
import lib.logger
from lib.config import duplicate
import logging
log = logging.getLogger(__name__)


class MasterError(Exception):
    """Generic Master error"""
    pass


class Master(object):
    """creates a buildbot master"""
    def __init__(self, configuration):
        self.configuration = configuration
        self.basedir = configuration.get('master', 'basedir')
        self.buildbot_configs_repo = configuration.get('master',
                                                       'buildbot_configs_repo')

    def install(self):
        """installs buildbot master"""
        self._prepare_dirs()
        tmp_dir = tempfile.mkdtemp()
        log.info('installing buildbot master')
        log.debug('tmp_dir: {0}'.format(tmp_dir))
        self._clone_builbot_configs(tmp_dir)
        self._make(tmp_dir)
        self.write_master_json()
        shutil.rmtree(tmp_dir)

    def _prepare_dirs(self):
        """creates required directories
           rises a MasterError if directories are already in place."""
        # If a directory already exists, probably, this script
        # probaly this script has been executed
        try:
            os.makedirs(self.basedir)
        except OSError as error:
            msg = 'Cannot create: {0} ({1})'.format(self.basedir, error)
            raise MasterError(msg)

    def _clone_builbot_configs(self, target_dir):
        """clones buildbot-configs into target_dir"""
        log.info('cloning {0}'.format(self.buildbot_configs_repo))
        hg_cmd = ('clone', self.buildbot_configs_repo, target_dir)
        for line in hg(hg_cmd, _iter=True):
            log.debug(line.strip())

    def _make(self, cwd):
        """calls make to create a buildbot master"""
        log.info('creating master in {0}'.format(self.basedir))
        config = self.configuration
        make_cmd = config.get('master', 'make_cmd').splitlines()
        log.debug('make command: {0}'.format(make_cmd))

        for line in make(make_cmd, _cwd=cwd, _iter=True):
            log.debug(line.strip())

    def start(self):
        """starts a master instance"""
        make('start', _cwd=self.basedir)

    def stop(self):
        """stops a master instance"""
        make('stops', _cwd=self.basedir)

    def checkconfig(self):
        """checks master configuration"""
        make('checkconfig', _cwd=self.basedir)

    def write_master_json(self):
        conf = self.configuration
        src_json_ini = conf.get('master', 'src_json_ini')
        dst_json = conf.get('master', 'dst_json')
        mj = MasterJson(self.configuration, src_json_ini)
        mj.write(dst_json)


class MasterJson(object):
    def __init__(self, configuration, src_ini_file):
        self.section = 'master_json'
        config = duplicate(configuration)
        config.read(src_ini_file)
        self.configuration = config

    def _limit_keys(self):
        limits = []
        conf = self.configuration
        for limit in conf.get(self.section, 'limit_keys').split(','):
            if limit:
                limits.append(conf._sections[limit])
        return limits

    def write(self, dst):
        # json file == this section + limit branches
        # just a work in progress
        conf = self.configuration
        print conf
