"""creates and cofigures a staging master"""
import os
import json
from sh import make
from lib.config import duplicate
from lib.repositories import Repository, RepositoryError

from lib.logger import logger
log = logger(__name__)


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
        log.info('installing buildbot master')
        self._clone_repositories()

    def _prepare_dirs(self):
        """creates required directories
           rises a MasterError if directories are already in place."""
        # If a directory already exists, probably
        # this has already been executed
        try:
            os.makedirs(self.basedir)
        except OSError as error:
            msg = 'Cannot create: {0} ({1})'.format(self.basedir, error)
            raise MasterError(msg)

    def _to_canoical_name(self, repo_name):
        config = self.configuration
        bug = config.get('common', 'tracking_bug')
        bug = '-{0}'.format(bug)
        name = repo_name.split('/')[-1]
        if name.endswith(bug):
            name = name.partition(bug)[0]
        log.debug('canonical name: {0} => {1}'.format(repo_name, name))
        return name

    def _clone_repositories(self):
        """clones buildbot-configs"""
        config = self.configuration
        repos = config.get('master', 'repositories').split(',')
        for repo in repos:
            dst_dir = os.path.join(self.basedir,
                                   self._to_canoical_name(repo))
            log.info('cloning {0} to {1}'.format(repo, dst_dir))
            self._clone_hg_repo(repo, dst_dir)

    def _make(self, cwd):
        """calls make to create a buildbot master"""
        log.info('creating master in {0}'.format(self.basedir))
        config = self.configuration
        make_cmd = config.get('master', 'make_cmd').splitlines()
        # remove empty lines
        make_cmd = [option for option in make_cmd if option]
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

    def _clone_hg_repo(self, name, dst_dir, branch='default'):
        try:
            repo = Repository(self.configuration, name)
            repo.clone_locally(dst_dir, branch)
        except RepositoryError as error:
            log.error(error)
            raise MasterError(error)


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
