#!/bin/bash

#https://wiki.mozilla.org/ReleaseEngineering/How_To/Setup_Personal_Development_Master#Create_a_build_master
#https://wiki.mozilla.org/Release:Release_Automation_on_Mercurial:Staging_Specific_Notes
set -e
cd "$(dirname $0)"
CURRENT_DIR="$(pwd)"
USERNAME="$(whoami)"
GROUP="$(id -ng)"
ROLE="build"
BASEDIR="/builds/buildbot/$USERNAME"
SHIPIT_DIR="$BASEDIR/release-kickoff"
SHIPIT_USER="shipit"
PASSWORD="$(openssl rand -base64 7 | sed 's/=//g' | sed 's!/!!g')"

echo ""
echo "Setting up a ship it for staging releases"
echo "========================================="
if [ -e "$SHIPIT_DIR" ]
then
    echo "$SHIPIT_DIR already exists: terminating"
    echo "stop, backup and remove your $SHIPIT_DIR if you want to run this script"
    exit 0
fi

echo "* cloning ship it from github"
cd "$BASEDIR"
git clone https://git.mozilla.org/build/release-kickoff.git > /dev/null 2>&1
cd release-kickoff
echo "* creating virtualenv"
virtualenv-2.6 venv > /dev/null 2>&1
echo "* installing required packages"
venv/bin/pip install -r requirements/dev.txt > /dev/null 2>&1

#====================#
# finding free ports #
#====================#
# create a library and put random port functions into a single place
function shipit_port {
    echo $((5000 +$1))
}

#### beautiful solution provided by Pete ####
function port_suffix {
    while true; do
        portsuffix=$[RANDOM % 1000]
        SHIPIT_PORT=$(shipit_port $portsuffix)
        if (! nc -z 127.0.0.1 $SHIPIT_PORT) > /dev/null
        then
            echo $portsuffix
            break
        fi
    done
}

port_suffix=$(port_suffix)
SHIPIT_PORT="$(shipit_port $port_suffix)"
echo "#!/bin/bash" > "$SHIPIT_DIR/start_shipit.sh"
echo 'cd $(dirname$0)' >> "$SHIPIT_DIR/start_shipit.sh"
echo "echo '* http://dev-master01.build.scl1.mozilla.com:$SHIPIT_PORT/'" >> "$SHIPIT_DIR/start_shipit.sh"
echo "echo '* user: $SHIPIT_USER'" >> "$SHIPIT_DIR/start_shipit.sh"
echo "echo '* password: $PASSWORD'" >> "$SHIPIT_DIR/start_shipit.sh"
echo "$SHIPIT_DIR/venv/bin/python $SHIPIT_DIR/kickoff-web.py -d sqlite:///kickoff.db -u $SHIPIT_USER -p $PASSWORD --host=0.0.0.0 --port=$SHIPIT_PORT" >> "$SHIPIT_DIR/start_shipit.sh"

chmod u+x "$SHIPIT_DIR/start_shipit.sh"
echo "to start shipit, run: $SHIPIT_DIR/start_shipit.sh"
echo "* http://dev-master01.build.scl1.mozilla.com:$SHIPIT_PORT/"
echo "* user: $SHIPIT_USER"
echo "* password: $PASSWORD"
