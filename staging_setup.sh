#!/bin/bash

#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master
set -e
cd "$(dirname $0)"
CURRENT_DIR="$(pwd)"
USERNAME="$(whoami)"
GROUP="$(id -ng)"
ROLE="build"
BASEDIR="/builds/buildbot/$USERNAME/staging"
MASTER_DIR="$BASEDIR/master"

echo ""
echo "Setting up a new build master for staging releases"
echo "=================================================="
if [ -e "$BASEDIR" ]
then
    echo "$BASEDIR already exists: terminating"
    echo "stop, backup and remove your $BASEDIR if you want to run this script"
    exit 0
fi


TMP_DIR="$(mktemp -d -t XXXXXXXX)"
trap "rm -f $TMP_DIR" EXIT
cd "$TMP_DIR"
#====================#
# finding free ports #
#====================#

function http_port {
    echo $((8000 + $1))
}
function ssh_port {
    echo $((7000 +$1))
}
function pb_port {
    echo $((9000 +$1))
}

#### beautiful solution provided by Pete ####
function port_suffix {
    while true; do
        portsuffix=$[RANDOM % 1000]
        SSH_PORT=$(ssh_port $portsuffix)
        HTTP_PORT=$(http_port $portsuffix)
        PB_PORT=$(pb_port $portsuffix)
        if (! nc -z 127.0.0.1 $SSH_PORT || \
            ! nc -z 127.0.0.1 $HTTP_PORT || \
            ! nc -z 127.0.0.1 $PB_PORT)>/dev/null
        then
            echo $portsuffix
            break
        fi
    done
}

function detokenize {
    SRC_FILE=$1
(
IFS=
while read -r TOKEN_LINE
do
    eval "echo \"$(echo "$TOKEN_LINE" | sed 's/\\/\\\\/g;s/\"/\\\"/g;s/\$[^{(]/\\&/g')\""
done < "$SRC_FILE"
)

}
#### end ####
portsuffix=$(port_suffix)
SSH_PORT=$(ssh_port $portsuffix)
HTTP_PORT=$(http_port $portsuffix)
PB_PORT=$(pb_port $portsuffix)

#===============#
# create master #
#===============#
echo "* cloning buildbot-configs repository"
hg clone http://hg.mozilla.org/build/buildbot-configs > /dev/null 2>&1
cd buildbot-configs

echo "* running make -f Makefile.setup"
make -f Makefile.setup \
USE_DEV_MASTER=1 \
MASTER_NAME="$USERNAME" \
BASEDIR="$BASEDIR" \
PYTHON=python2.6 \
VIRTUALENV=virtualenv-2.6 \
BUILDBOTCUSTOM_BRANCH=default \
BUILDBOTCONFIGS_BRANCH=default \
USER="$USERNAME" \
HTTP_PORT="$HTTP_PORT" PB_PORT="$PB_PORT" SSH_PORT="$SSH_PORT" ROLE="$ROLE" \
virtualenv deps install-buildbot master master-makefile > /dev/null 2>&1
cd "$BASEDIR"
rm -rf "$TMP_DIR"

echo "* creating master_config.json"
CONFIG_JSON="$CURRENT_DIR/staging_config.json"
(detokenize "$CONFIG_JSON") > "$MASTER_DIR/master_config.json"

echo "* using universal master sqlite configruation file"
rm -rf "$MASTER_DIR/master.cfg"
ln -s "$BASEDIR/buildbot-configs/mozilla/universal_master_sqlite.cfg" "$MASTER_DIR/master.cfg"

if [ -e "$HOME/passwords.py" ]
then
    cp "$HOME/passwords.py" "$MASTER_DIR"
else
    echo "* NOTE: You may need to populate master/passwords.py so the download_token step doesn't fail."
fi
echo "* NOTE: Add branches of interest to master/master_config.json limit_branches, release_branches, etc."
make checkconfig
set +e
make start || grep 'configuration update complete' master/twistd.log || exit 64
echo "buildbot master: http://dev-master01.build.scl1.mozilla.com:$HTTP_PORT/"
