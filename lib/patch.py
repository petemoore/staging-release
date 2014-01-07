"""Updates user's repository configuration files"""

import os
import shutil
import tempfile
from lib.logger import logger
from lib.repositories import Repository
log = logger(__name__)


class PatchError(Exception):
    """Generic Patch error"""
    pass


class Patch(object):
    """
    Updates user's repositories so configuration points to the right location
    """
    def __init__(self, configuration, release_type):
        assert isinstance(release_type, (list, tuple))
        self.release_type = list(release_type)
        self.repository = None
        self.tokens = configuration.get_list('patch', 'tokens')
        self.configuration = configuration

    def clone(self, repository):
        self._create_temp_dir()
        log.debug('temporary directory: {0}'.format(self.dst_dir))
        repo = Repository(self.configuration, repository)
        log.info('cloning: {0}'.format(repository))
        repo.clone_locally(self.dst_dir)
        self.repository = repo

    def update_configs(self):
        files = self._files_to_update()
        conf = self.configuration
        username = conf.get('common', 'username')
        bug = conf.get('common', 'tracking_bug')
        repo_names = conf.options('repositories')
        repos = repositories_map(repo_names, username, bug)
        tokens = self.tokens
        log.debug('tokens: {0}'.format(tokens))
        for repo in repos:
            # replace build/<repo> with users/... repo
            mozilla_repo, user_repo = repos[repo]
            for conf_in in files:
                # in every file...
                log.info('patching: {0}'.format(conf_in))
                out = []
                f_in = open(conf_in, 'r')
                for line in f_in:
                    for token in tokens:
                        if mozilla_repo in line and not 'raw-file' in line:
                            log.debug(line)
                            log.debug('{0} => {1}'.format(mozilla_repo,
                                                          user_repo))
                            line = line.replace(mozilla_repo, user_repo)
                            log.debug(line)
                    out.append(line)
                f_in.close()
            # write file before
            log.debug('writing changes to: {0}'.format(conf_in))
            with open(conf_in, 'w') as out_f:
                for line in out:
                    out_f.write(line)

    def commit_changes(self):
        log.info('committing local changes')

    def _create_temp_dir(self):
        self.dst_dir = tempfile.mkdtemp()

    def _delete_temp_dir(self):
        try:
            shutil.rmtree(self.dst_dir)
        except Exception as error:
            # cannot delete temp dir
            log.debug('Patch: failed to delete temporary directory')
            log.debug(error)

    def push_changes(self):
        log.info('pushing changes to remote')

    def _files_to_update(self):
        config = self.configuration
        files = self.release_type
        files.append('common_files')
        files.append('l10n')
        staging_files = []
        for element in files:
            config_files = config.get_list('staging_files', element)
            log.debug(config_files)
            staging_files.extend(config_files)
        # get the absolute path
        staging_files = [os.path.join(self.dst_dir, f) for f in staging_files]
        # remove not existing files
        staging_files = [f for f in staging_files if os.path.exists(f)]
        log.debug('files to be patched: {0}'.format(set(staging_files)))
        return set(staging_files)

    def _absoulute_path(self, filename):
        try:
            return os.path.join(self.dst_dir, filename)
        except TypeError as error:
            log.debug(error)

    def fix(self, repository):
        log.info('updating configuration for staging release')
        self.clone(repository)
        self.update_configs()
        self.commit_changes()
        self.push_changes()


def make_user_repo(line, tracking_bug):
    sep = 'build/'
    quote = "'"
    if sep in line:
        pre, sep, post = line.partition(sep)
        #'config_repo_path': 'build/buildbot-configs'
        #<       pre        >|<sep>|<      post     >
        if quote in pre:
            # values are single quote separated
            pass
        else:
            # values are double quote separated
            quote = '"'
        repo_name, sep, post = post.partition(quote)
        repo_name = '{0}-{1}{2}'.format(repo_name, tracking_bug, post)
        return '{0}/user/{_mozilla.org'


def repositories_map(repository_names, username, tracking_bug):
    """Creates a map of the mozilla repo <-> user repo names"""
    my_map = {}
    for repo in repository_names:
        my_map[repo] = ('build/{0}'.format(repo),
                        'users/{0}_mozilla.com/{1}-{2}'.format(username,
                                                               repo,
                                                               tracking_bug))
    # replace stage-ffxbld -> username_mozilla.com
 #   my_map['stage-ffxbld'] = ('users/stage-ffxbld',
 #                             'users/{0}_mozilla.com'.format(username))
    return my_map
