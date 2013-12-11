"""
some quick tests
"""
from lib.config import Config
from lib.master import MasterJson
import lib.locales as locales


if __name__ == '__main__':
    config = Config()
    mj = MasterJson(config, 'master_config.json.ini')
    mj.write('')
#    config.read('config.ini')
#    url = config.get('locales', 'url')
#    locales = locales.get_shipped_locales(url)
#    print locales
