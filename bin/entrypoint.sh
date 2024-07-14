#!/bin/bash

set -euo pipefail 

echo "Storing ENV variables in /etc/environment"
printenv | grep -Ev '(^_|^PWD|_SERVICE_|_TCP_|_PORT)' | awk -F '=' '{print $1"=\""$2"\""}' >> /etc/environment


if [[ "${PROFILE:=}" == "snap" ]]; then
    echo "Enabling snapshot service"
    sed -e "s/^autostart=false/autostart=true/" -i /etc/supervisor.d/snapshot.conf
fi

#/usr/local/bin/cvcontrol.py start

exec $@
