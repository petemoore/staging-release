"""
download the list of locales
"""
import urllib2


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
    except urllib2.HTTPError as e:
        msg = 'HTTPError = {0}\n'.format(str(e.code))
        msg = '{0}url: {1}'.format(locales_url)
        raise NoLocalesError(msg)
    except urllib2.URLError as e:
        msg = 'URLError = {0}'.format(e.reason)
        msg = '{0}url: {1}'.format(locales_url)
        raise NoLocalesError(msg)
    for line in data:
        locales.append(line.strip())
    # removing empty lines
    return tuple([locale for locale in locales if locale is not None])
