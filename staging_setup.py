#!/usr/bin/env python

#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master
import os
from lib.config import Config
from lib.master import Master, MasterError
from lib.shipit import Shipit, ShipitError
import lib.logger
import logging
import argparse

if __name__ == '__main__':

    log = logging.getLogger('staging release')

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bug', help='bug tracking id', required=True)
    args = parser.parse_args()

    # reading configuration
    config = Config()
    config_ini = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read_from(config_ini)
    config.set('DEFAULT', 'tracking_bug', args.bug)
    log.info(config)
    master = Master(config)
    shipit = Shipit(config)
    try:
        master.install()
        shipit.install()

    except MasterError as error:
        log.error('unable to install buildbot master: ', error)
    except ShipitError as error:
        log.error('unable to install shipit: ', error)
