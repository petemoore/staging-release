"""
This module manages the cloning mozilla hg repos into user repos.
Created user repositories are named after the original repository
adding -self.bug (tracking bug id from bugzilla) to already existing user
repositories are not deleted.
Please not that this module can be very dangerous
"""

import os
from sh import ssh, hg
from sh import ErrorReturnCode_1, ErrorReturnCode
import shutil
import tempfile

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
        cmd = ('hg.mozilla.org', 'clone', dst_repo_name,  src_repo_name)
        log.info('cloning {0} to {1}'.format(src_repo_name, dst_repo_name))
        log.debug('running ssh {0}'.format(' '.join(cmd)))
        ssh(cmd)

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
            for line in ssh(cmd, _iter=True):
                out = line.strip()
                log.debug(out)
                output.append(out)
        except ErrorReturnCode_1:
            log.debug('trying to delete a non existing repo... pass')
        except ErrorReturnCode:
            msg = 'bad exit code executing {0}'.format(' '.join(cmd))
            log.error(msg)
            raise RepositoryError(msg)

    def clone_locally(self, dst_dir, branch='default', clone_from='user'):
        """clones the repo into dst_dir"""
        conf = self.configuration
        repo = conf.get(self.name, 'mozilla_repo')
        if clone_from != 'mozilla':
            repo = conf.get(self.name, 'user_repo')
        cmd = ('clone', repo, dst_dir)
        log.debug('running sh {0}'.format(' '.join(cmd)))
        self.local_checkout_dir = dst_dir
        hg_cmd = ('clone', '-b', branch, repo, dst_dir)
        try:
            for line in hg(hg_cmd, _iter=True):
                log.debug(line.strip())
        except ErrorReturnCode as error:
            msg = 'clone failed'
            msg = '{0}: hg {1}'.format(msg, ' '.join(cmd))
            msg = '{0} - error: {1}'.format(msg, error)
            log.debug(msg)
            raise RepositoryError('clone failed')

    def commit(self, commit_message):
        """commit local changes"""
        try:
            cmd = ('commit', '-m', commit_message)
            for line in hg(cmd, _cwd=self.local_checkout_dir):
                log.debug(line.strip())
        except ErrorReturnCode as error:
            msg = 'commit failed: {0}'.format(error)
            raise RepositoryError(msg)

    def _update_hgrc(self):
        """adds defaut-push in .hgrc"""
        hg_rc = os.path.join(self.local_checkout_dir, '.hg', 'hgrc')
        import configparser
        hgrc = configparser.ConfigParser()
        hgrc.read(hg_rc)
        default = str(hgrc.get('paths', 'default'))
        # DO NOT PUSH TO hg.m.o/build/<repo>
        if 'hg.mozilla.com/build' in default or \
           'hg.mozilla.org/build' in default:
            msg = 'cowardly refusing to push to hg.m.o/build'
            msg = '{0} - (please use hg.m.o/users/<repo> instead)'.format(msg)
            raise RepositoryError(msg)
        # casting to str because pylint wants it
        # replace https or http with ssh
        default_push = default.replace('https:', 'ssh:')
        default_push = default.replace('http:', 'ssh:')
        hgrc.set('paths', 'default-push', default_push)
        with open(hg_rc, 'wb') as configfile:
            hgrc.write(configfile)

        # log .hg/hgrc content
        with open(hg_rc, 'r') as configfile:
            for line in configfile:
                log.debug(line.strip())

    def push(self):
        """pushes local changes to the remote repository"""
        self._update_hgrc()
        try:
            # logging what is about to be pushed
            cmd = ('out', '-p', '--color', 'never')
            for line in hg(cmd, _cwd=self.local_checkout_dir):
                log.debug(line.strip())
            # and now log the push command
            lines = []
            # hg('push', _cwd=self.local_checkout_dir)
            for line in lines:
                log.debug(line.strip())
        except ErrorReturnCode as error:
            msg = 'push failed: {0}'.format(error)
            log.debug(msg)
            raise RepositoryError(msg)

    def tag(self, tag='default'):
        """tags a repository with tag, if tag is not provided,
           it will use tag_name function do determine the tag"""
        conf = self.configuration
        if tag == 'default':
            products = conf.get_list('common', 'staging_release')
            version = conf.get('common', 'version')
            tag = tag_name(version, products)
        try:
            cmd = ('tag', '-f', tag)
            for line in hg(cmd, _cwd=self.local_checkout_dir):
                log.debug(line.strip())
        except ErrorReturnCode as error:
            msg = 'tag failed: {0}'.format(error)
            log.debug(msg)
            raise RepositoryError(msg)


class Repositories(object):
    """Manages repositories in configuration"""
    def __init__(self, configuration):
        self.configuration = configuration

    def prepare_user_repos(self):
        """runs delete, create, clone and tag on every repository"""
        conf = self.configuration
        repos = conf.options('repositories')
        for repo in repos:
            log.info(repo)
            repo = Repository(conf, repo)
            repo.delete_user_repo()
            repo.create_repo()
            dst_dir = tempfile.mkdtemp()
            repo.clone_locally(dst_dir, clone_from='user')
            repo.tag()
            repo.push()
            shutil.rmtree(dst_dir)


def tag_name(version, products):
    """returns the tag name"""
    names = []
    version = version.replace('.', '_')
    for name in products:
        names.append('{0}_{1}_RELEASE'.format(name.upper(), version))
    return ', '.join(names)


def to_user_repo(repo_name, tracking_bug):
    """transforms mozilla's (build) repository to user's repo
        e.g. tools => tools-9999
    """
    return '{0}-{1}'.format(repo_name, tracking_bug)


def to_mozilla(repo_name, tracking_bug):
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
