"""
This module manages the cloning mozilla hg repos into user repos.
Created user repositories are named after the original repository
adding -self.bug (tracking bug id from bugzilla) to already existing user
repositories are not deleted.
Please not that this module can be very dangerous
"""
import lib.locales as locales
from sh import ssh

from lib.logger import logger
log = logger(__name__)


class RepositoryError(Exception):
    """
    Something failed during clone/delete phases
    """
    pass


class Repositories(object):
    """
    this class manages the creation and deleting of hg user repo
    this class can be very dangerous
    """
    def __init__(self, configuration, username, tracking_bug):
        self.config = configuration
        self.username = username
        self.bug = tracking_bug
        self.locales = None

    def repos_name(self):
        """
        returns a list of repositories that will be cloned by this object
        """
        config = self.config
        return config.options('repositories')

    def prepare(self):
        """clones mozilla build/<repo>
           into .../users/<username>_mozilla.com/<repo>-bug
           ACHTUNG
           prepare has 2 steps:
           1) DELETE .../users/<username>_mozilla.com/<repo>-bug
           2) fresh clone of mozilla repo into user's repo
        """
        for repo in self.repos_name():
            src_repo = "build/{0}".format(repo)
            dst_repo = "{0}-{1}".format(repo, self.bug)
            self._delete_user_repo(dst_repo)
            self._clone_into_user_repo(src_repo, dst_repo)

        # locales
        for locale in self._locales_list():
            src_repo = "l10n-central/{0}".format(locale)
            dst_repo = "{0}-{1}".format(locale, self.bug)
            self._delete_user_repo(dst_repo)
            self._clone_into_user_repo(src_repo, dst_repo)

            # add mozilla central here or update config.ini
            # ssh hg.mozilla.org edit mozilla-central delete YES
            # ssh hg.mozilla.org clone mozilla-central mozilla-central

    def _clone_into_user_repo(self, src_repo, dst_repo):
        """clones mozilla's repo into user's repo"""
        suffix = '-{0}'.format(self.bug)
        if not dst_repo.endswith(suffix):
            msg = "cowardly refusing to delete {0}".format(dst_repo)
            msg = "{0}, if does not end with {1}".format(msg, suffix)
            raise RepositoryError(msg)
        ssh("hg.mozilla.org", "clone", dst_repo, src_repo)

    def _delete_user_repo(self, repository_name):
        """deletes user's repository <name>-<bug>
        """
        suffix = "-{0}".format(self.bug)
        if not repository_name.endswith(suffix):
            msg = "cowardly refusing to delete {0}".format(repository_name)
            msg = "{0}, if does not end with -{1}".format(msg, self.bug)
            raise RepositoryError(msg)
        ssh("hg.mozilla.org", "edit", repository_name,  "delete", "YES")

    def _locales_list(self):
        """
        gets the list of shipped locales (en-US is excluded from this list)
        """
        if self.locales:
            return self.locales
        conf = self.config
        url = conf.get('locales', 'url')
        try:
            self.locales = locales.get_shipped_locales(url)
        except locales.NoLocalesError as error:
            raise RepositoryError(error)
        return self.locales
