#!/usr/bin/env python

#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master
import os
from lib.config import Config
from lib.master import Master
from lib.master import MasterError
import lib.logger
import logging


if __name__ == '__main__':

    log = logging.getLogger('staging release')
    # reading configuration
    config = Config()
    config_ini = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read_from(config_ini)
    master = Master(config)
    try:
        master.install()
    except MasterError as error:
        msg = 'master creation failed with the following error: {0}'.format(error)
        log.error(msg)
