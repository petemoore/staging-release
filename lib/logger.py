"""Log manager
   import this module if you need to log
"""
import logging.config
import os.path

logging_conf = os.path.join(os.path.dirname(__file__), '..', 'logging.ini')
logging.config.fileConfig(logging_conf)


def logger(name):
    return logging.getLogger(name)
