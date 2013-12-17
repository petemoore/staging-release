"""
some quick tests
"""
#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master
import sh
import os
import shutil
from lib.config import Config
from lib.master import MasterJson
#from lib.master import Master, MasterError
#from lib.shipit import Shipit, ShipitError
#from lib.releaserunner import ReleaseRunner, ReleaseRunnerError
from lib.buildbotconfigs import BuildbotConfigs
#from lib.buildbotconfigs import BuildbotConfigs, BuildbotConfigsError
from lib.logger import logger
#import lib.locales as locales
import argparse


def replace_in(filename, src_name, dst_name):
    import tempfile
    print "{0}: {1}->{2}".format(filename, src_name, dst_name)
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    with open(tmp_file.name, 'w') as out:
        with open(filename, 'r') as script:
            for line in script:
                print line.strip()
                if src_repo in line:
                    print '**** {0}'.format(line)
                    line = line.replace(src_name, dst_name)
                out.write(line)
    shutil.move(tmp_file.name, filename)


def release_files(configuration):
    staging_release = configuration.get('common', 'staging_release').split(',')
    files = set()
    for release in staging_release:
        staging_files = config.get('staging_files', release)
        staging_files = staging_files.split(',')
        for element in staging_files:
            files.add(os.path.join(tmp_dir, element.strip()))
    return files


if __name__ == '__main__':

    log = logger('staging release')

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bug', help='bug tracking id', required=True)
    msg = 'staging release comma separated values (e.g: firefox,fennec)'
    parser.add_argument('-r', '--release', help=msg, required=True)
    args = parser.parse_args()

    # reading configuration
    config = Config()
    config_ini = os.path.join(os.path.dirname(__file__), "config.ini")
    config.read_from(config_ini)
    config.set('common', 'tracking_bug', args.bug)
    config.set('common', 'staging_release', args.release)
    mj = MasterJson(config, 'master_config.json.ini')
    mj.write('')

    bc = BuildbotConfigs(config)
#    url = config.get('locales', 'url')
#    locales = locales.get_shipped_locales(url)
#    print locales
#    bc.delete_user_repo()
#    bc.create_repo()
    tmp_dir = '/tmp/bc-conf'
#    shutil.rmtree(tmp_dir, ignore_errors=True)
#    bc.clone_locally('/tmp/bc-conf')
    bc.local_checkout_dir = tmp_dir
    #bc.prepare_for_staging()

    sh.hg('revert', '--all', _cwd=tmp_dir)
    replace_me = list()
    username = config.get('common', 'username')
    bug = config.get('common', 'tracking_bug')
    for repo in config.options('repositories'):
        src_repo = config.get(repo, 'src_repo_name')
        dst_repo = config.get(repo, 'dst_repo_name')
        src_repo = "{0}".format(src_repo)
        dst_repo = "{0}".format(dst_repo)
        a = (src_repo, dst_repo)
        replace_me.append(a)
        #fx_repo = 'users/stage-ffxbld/{0}'.format(repo)
        #user_repo = 'users/{0}_mozilla.com/{1}-{2}'.format(username, repo, bug)
        #a = (fx_repo, user_repo)
        #replace_me.append(a)

    files = release_files(config)
    for script in files:
        for token in replace_me:
            print "{0} -> {1}".format(token[0], token[1])
            replace_in(script, token[0], token[1])
        break
