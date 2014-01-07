#!/usr/bin/env python

#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master
import os
from lib.config import Config
from lib.repositories import Repositories, RepositoryError
from lib.patch import Patch, PatchError
from lib.logger import logger
import argparse

if __name__ == '__main__':

    log = logger('staging release')

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cfg', help='configuration file', required=True)
    parser.add_argument('-b', '--bug', help='bug tracking id', required=True)
    msg = 'staging release comma separated values (e.g: firefox,fennec)'
    parser.add_argument('-r', '--release', help=msg, required=True)
    msg = 'username: if not specified, whoami will be used'
    parser.add_argument('-u', '--username', help=msg)
    args = parser.parse_args()

    # reading configuration
    config = Config()
    config_ini = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read_from(args.cfg)
    config.set('common', 'tracking_bug', args.bug)
    config.set('common', 'staging_release', args.release)
    if args.username:
        config.set('common', 'username', args.username)
    log.debug(config)
    relese_type = config.get_list('common', 'staging_release')
    patch = Patch(config, relese_type)
    repositories = Repositories(config)
    try:
        repositories.prepare_user_repos()
        patch.fix('buildbot-configs')
    except PatchError as error:
        log.error('unable to patch user repositories: {0}'.format(error))
    except RepositoryError as error:
        log.error('unable to create user repositories: {0}'.format(error))
