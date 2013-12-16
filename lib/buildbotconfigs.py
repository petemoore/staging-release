import os
import sh
import shutil
import tempfile

from lib.logger import logger
log = logger(__name__)


class BuildbotConfigsError(Exception):
    """Generic BuildbotConfigs Eerror"""


class BuildbotConfigs(object):
    """Virtualenv class, creates a virtualenv"""
    def __init__(self, configuration):
        self.configuration = configuration
        self.name = configuration.get('buildbot-configs', 'name')
        self.bug = configuration.get('common', 'tracking_bug')
        self.local_checkout_dir = None

    def create_repo(self):
        """creates a buildbot-configs repo as
           a copy of https://hg.mozilla.org/build/buildbot-configs/
           It creates hg.m.o/users/<ldap>_mozilla.com/buildbot-configs-<bug>
           appending -<bug> because this script creates and destroys that
           repo without asking for user permission.

        """
        conf = self.configuration
        src_repo_name = conf.get('buildbot-configs', 'src_repo_name')
        dst_repo_name = conf.get('buildbot-configs', 'dst_repo_name')
        if not dst_repo_name.endswith(self.bug):
            msg = "cowardly refusing to clone {0}".format(dst_repo_name)
            msg = "{0}, its name does not end with {1}".format(msg, self.bug)
            log.error(msg)
            raise BuildbotConfigsError(msg)
        cmd = ("hg.mozilla.org", "clone", dst_repo_name,  src_repo_name)
        log.info('cloning {0} to {1}'.format(src_repo_name, dst_repo_name))
        log.debug('running ssh {0}'.format(' '.join(cmd)))
        sh.ssh(cmd)

    def delete_user_repo(self):
        """delete user's remote repository"""
        conf = self.configuration
        dst_repo_name = conf.get('buildbot-configs', 'dst_repo_name')
        if not dst_repo_name.endswith(self.bug):
            msg = "cowardly refusing to delete {0}".format(dst_repo_name)
            msg = "{0}, its name does not end with {1}".format(msg, self.bug)
            log.error(msg)
            raise BuildbotConfigsError(msg)
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
            raise BuildbotConfigsError(msg)

    def clone_locally(self, dst_dir):
        """clones the repo into dst_dir"""
        conf = self.configuration
        repo = conf.get('buildbot-configs', 'repo')
        cmd = ('clone', repo, dst_dir)
        log.debug('running sh {0}'.format(' '.join(cmd)))
        self.local_checkout_dir = dst_dir
        try:
            sh.hg('clone', repo, dst_dir)
        except sh.ErrorReturnCode as error:
            msg = 'clone failed'
            msg = '{0}: hg {1}'.format(msg, ' '.join(cmd))
            msg = '{0} - error: {1}'.format(msg, error)
            log.debug(msg)
            raise BuildbotConfigsError('clone failed')

    def prepare_for_staging(self):
        """updates the references to build/... -> users/...
           of a local checkout.
        """
        if not self.local_checkout_dir:
            msg = 'prepare for staging failed: local checkout does not exist'
            raise BuildbotConfigsError(msg)
        files = set()
        for root, dirs, files in os.walk(self.local_checkout_dir):
            for script in files:
                if script.endswith('.py'):
                    with open(os.path.join(root, script)) as src:
                        for line in src.readlines():
                            if 'build/' in line and 'test' not in line:
                                files.add(os.path.join(root, script))

        files = filter(lambda k: 'test' not in k, files)
        files = filter(lambda k: 'calendar' not in k, files)
        files = filter(lambda k: 'seamonkey' not in k, files)
        files = filter(lambda k: 'b2g' not in k, files)
        return files


def update_to_user_repo(configuration, filename):
    """Updates repositories name in place;
       from build/<repo> to users/<ldap>_mozilla.com/<repo>-<bug>
    """

    username = configuration.get('common', 'username')
    bug = configuration.get('common', 'tracking_bug')
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    with open(tmp_file.name, 'w') as out:
        with open(filename, 'r') as script:
            print filename
            for line in script:
                if 'build' in line:
                    before, sep, after = line.partition('build/')
                    sep = 'users/{0}_mozilla.com'.format(username)
                    repo = after.partition('/')[0].partition("'")[0]
                    repo = '{0}-{1}'.format(repo, bug)
                    updated_line = ''.join(before, sep, repo)
                    print updated_line
                    out.write(updated_line)
                else:
                    out.write(line)
    shutil.move(tmp_file.name, filename)
