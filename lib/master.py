"""creates and cofigures a staging master"""
import os
import sh
import subprocess
from lib.venv import Virtualenv
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
        self.venv = None

    def install(self):
        """installs buildbot master"""
        self._prepare_dirs()
        log.info('installing buildbot master')
        self.virtualenv()
        self.deps()
        self.install_buildbot()
        self.master()
        self.master_makefile()

    def master(self):
        """make master target"""
        config = self.configuration
        cmd = config.get('master', 'create_master').split(',')
        cmd = [line.strip() for line in cmd]
        cwd = os.path.join(self.basedir, 'buildbot-configs')
        script = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE)
        while True:
            log.debug(script.stdout.readline().strip())
            if script.poll() is not None:
                break

    def _prepare_dirs(self):
        """creates required directories
           rises a MasterError if directories are already in place."""
        # If a directory already exists, probably
        # this script has already been executed
        try:
            os.makedirs(self.basedir)
        except OSError as error:
            msg = 'Cannot create: {0} ({1})'.format(self.basedir, error)
            log.debug(msg)
            raise MasterError(msg)

    def _to_canoical_name(self, repo_name):
        """transforms user's repository name in standard repository names
           e.g. tools-9999 => tools
        """
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

    def start(self):
        """starts a master instance"""
        sh.make('start', _cwd=self.basedir)

    def stop(self):
        """stops a master instance"""
        sh.make('stops', _cwd=self.basedir)

    def checkconfig(self):
        """checks master configuration"""
        sh.make('checkconfig', _cwd=self.basedir)

    def _clone_hg_repo(self, name, dst_dir, branch='default'):
        """clone repository name to dst_dir
           where name is a section name in configuration
        """
        try:
            repo = Repository(self.configuration, name)
            repo.clone_locally(dst_dir, branch)
        except RepositoryError as error:
            log.error(error)
            raise MasterError(error)

    def virtualenv(self):
        """make virtualenv target"""
        conf = self.configuration
        extra_args = conf.get('master', 'virtualenv_extra_args').split(',')
        venv = Virtualenv(conf)
        venv.create(self.basedir, extra_args)
        self.venv = venv

    def deps(self):
        """make deps target"""
        conf = self.configuration
        req = conf.get('master', 'virtualenv_requirements').split(',')
        req = [line.strip() for line in req]
        venv = self.venv
        venv.install_dependencies(req)

    def install_buildbot(self):
        """make intall-buildbot target"""
        self._clone_repositories()
        self._generate_master_json()
        #$(VIRTUALENV_PYTHON) setup.py develop install
        conf = self.configuration
        args = conf.get('master', 'buildbot_install').split(',')
        args = [option.strip() for option in args]
        setup_py = conf.get('master', 'setup_py')
        venv = self.venv
        venv.setup_py(setup_py, args)
        # Get buildbotcustom and the build/tools library into PYTHONPATH
        # ln -sf $(BASEDIR)/buildbotcustom $(SITE_PACKAGES)/buildbotcustom
        site_packages = conf.get('master', 'site_packages')
        src_dir = conf.get('master', 'buildbot_configs_dir')
        dst_dir = os.path.join(site_packages, 'buildbotcustom')
        self._link(src_dir, dst_dir)

        # echo $BASEDIR/tools/lib/python > SITE_PACKAGES/build-tools-lib.pth
        pth_file = conf.get('master', 'pth_file')
        tools_python = conf.get('master', 'tools_python')
        with open(pth_file, 'a') as p_file:
            p_file.write(tools_python)

    def master_makefile(self):
        """make master-makefile"""
        #ln -sf $(BASEDIR)/buildbot-configs/Makefile.master $(BASEDIR)/Makefile
        conf = self.configuration
        src = conf.get('master', 'buildbotcustom_dir')
        src = os.path.join(src, 'Makefile.master')
        dst = os.path.join(self.basedir, 'Makefile')
        self._link(src, dst)

    def _link(self, src, dst):
        """creates a symlink and logs the operation."""
        # add windows support?
        # this should be a function not a method, create a base lib
        log.debug('creating symlink: {0} => {1}'.format(src, dst))
        os.symlink(src, dst)

    def _generate_master_json(self):
        """creates master.json file from a template"""
        conf = self.configuration
        json_template = conf.get('master', 'json_template')
        json_file = conf.get('master', 'dst_json')
        out_json = []
        with open(json_template, 'r') as json_in:
            for line in json_in:
                if '@' in line:
                    pre, sep, post = line.partition('@')
                    option = post.partition('@')[0]
                    value = conf.get('master', option.lower())
                    line = line.replace('@{0}@'.format(option), value)
                out_json.append(line)

        with open(json_file, 'w') as json_out:
            for line in out_json:
                json_out.write(line)
