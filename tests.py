"""
some quick tests
"""
from lib.config import Config
import lib.locales as locales


if __name__ == '__main__':
    config = Config()
    config.read('config.ini')
    url = config.get('locales', 'url')
    locales = locales.get_shipped_locales(url)
    print locales
