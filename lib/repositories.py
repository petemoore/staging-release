"""
This module manages the cloning mozilla hg repos into user repos.
Created user repositories are named after the original repository
adding -self.bug (tracking bug id from bugzilla) to already existing user
repositories are not deleted.
Please not that this module can be very dangerous
"""

from lib.logger import logger
log = logger(__name__)

import sh

from lib.logger import logger
log = logger(__name__)


class RepositoryError(Exception):
    """Generic Repository Eerror"""


class Repository(object):
    """Clones hg.m.o repositories into user's one
       manages checkouts and user's repository deletion
    """
    def __init__(self, configuration, name):
        self.configuration = configuration
        self.name = name
        self.bug = configuration.get('common', 'tracking_bug')
        self.local_checkout_dir = None

    def create_repo(self):
        """creates a reposiory as
           a copy of https://hg.mozilla.org/build/self.name/
           It creates hg.m.o/users/<ldap>_mozilla.com/self.name-<bug>
           appending -<bug> because this script creates and destroys that
           repo without asking for user permission.

        """
        conf = self.configuration
        src_repo_name = conf.get(self.name, 'src_repo_name')
        dst_repo_name = conf.get(self.name, 'dst_repo_name')
        if not dst_repo_name.endswith(self.bug):
            msg = "cowardly refusing to clone {0}".format(dst_repo_name)
            msg = "{0}, its name does not end with {1}".format(msg, self.bug)
            log.error(msg)
            raise RepositoryError(msg)
        cmd = ("hg.mozilla.org", "clone", dst_repo_name,  src_repo_name)
        log.info('cloning {0} to {1}'.format(src_repo_name, dst_repo_name))
        log.debug('running ssh {0}'.format(' '.join(cmd)))
        sh.ssh(cmd)

    def delete_user_repo(self):
        """delete user's remote repository"""
        conf = self.configuration
        dst_repo_name = conf.get(self.name, 'dst_repo_name')
        if not dst_repo_name.endswith(self.bug):
            msg = "cowardly refusing to delete {0}".format(dst_repo_name)
            msg = "{0}, its name does not end with {1}".format(msg, self.bug)
            log.error(msg)
            raise RepositoryError(msg)
        cmd = ("hg.mozilla.org", "edit", dst_repo_name,  "delete", "YES")
        log.info('deleting {0}'.format(dst_repo_name))
        log.debug('running ssh {0}'.format(' '.join(cmd)))
        output = []
        try:
            for line in sh.ssh(cmd, _iter=True):
                out = line.strip()
                log.debug(out)
                output.append(out)
        except sh.ErrorReturnCode_1:
            log.debug('trying to delete a non existing repo... pass')
            pass
        except sh.ErrorReturnCode:
            msg = 'bad exit code executing {0}'.format(' '.join(cmd))
            log.error(msg)
            raise RepositoryError(msg)

    def clone_locally(self, dst_dir, branch='default'):
        """clones the repo into dst_dir"""
        conf = self.configuration
        repo = conf.get(self.name, 'repo')
        cmd = ('clone', repo, dst_dir)
        log.debug('running sh {0}'.format(' '.join(cmd)))
        self.local_checkout_dir = dst_dir
        hg_cmd = ('clone', '-b', branch, repo, dst_dir)
        try:
            for line in sh.hg(hg_cmd, _iter=True):
                log.debug(line.strip())
        except sh.ErrorReturnCode as error:
            msg = 'clone failed'
            msg = '{0}: hg {1}'.format(msg, ' '.join(cmd))
            msg = '{0} - error: {1}'.format(msg, error)
            log.debug(msg)
            raise RepositoryError('clone failed')


class Repositories(Exception):
    def __init__(self, configuration):
        self.configuration = configuration

    def prepare_user_repos(self):
        conf = self.configuration
        repos = conf.options('repositories')
        for repo in repos:
            log.info(repo)
            repo = Repository(conf, repo)
            repo.delete_user_repo()
            repo.create_repo()


def to_user_repo(self, repo_name, tracking_bug):
    """transforms mozilla's (build) repository to user's repo
        e.g. tools => tools-9999
    """
    return '{0}-{1}'.format(repo_name, tracking_bug)


def to_mozilla(self, repo_name, tracking_bug):
    """transforms user's repository name in mozilla repository names
        e.g. build/tools-9999 => tools
        e.g. h.m.o/build/tools-9999 => tools
    """
    bug = '-{0}'.format(tracking_bug)
    name = repo_name.split('/')[-1]
    if name.endswith(tracking_bug):
        name = name.partition(bug)[0]
    log.debug('canonical name: {0} => {1}'.format(repo_name, name))
    return name


