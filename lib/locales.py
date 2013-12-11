"""
download the list of locales
"""
import urllib2

from lib.logger import logger
log = logger(__name__)


class NoLocalesError(Exception):
    """
    I am really sorry but there are no locales for you
    """
    pass


def get_shipped_locales(locales_url):
    """ returns a tuple containing the list of shipped locales
        taken from locales_url
    """
    locales = []
    try:
        data = urllib2.urlopen(locales_url)
    except urllib2.HTTPError as error:
        msg = 'HTTPError = {0}\n'.format(str(error.code))
        msg = '{0}url: {1}'.format(locales_url)
        log.error(msg)
        raise NoLocalesError(msg)
    except urllib2.URLError as error:
        msg = 'URLError = {0}'.format(error.reason)
        msg = '{0}url: {1}'.format(locales_url)
        log.error(msg)
        raise NoLocalesError(msg)
    for line in data:
        line = line.strip()
        # removing empty lines and line = en-US
        if line and line != 'en-US':
            locales.append(line.strip())
    log.debug('locales: {0}'.format(locales))
    return tuple(locales)
