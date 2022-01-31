#!/usr/bin/env bash

activated=$1


if [ $activated != "on" ] && [ $activated != "off" ]; then
    echo "This script activates or deactivates gmv nexus repository in ~/.config/pip/pip.conf . Two options: on or off"
    exit
fi

if [ $activated = "on" ];
then
echo '
[global]
timeout = 60
index-url = https://shared:g4LL1f4nt3*@dev-tools.labs.gmv.com/nexus/repository/public_pypi/simple
index = https://shared:g4LL1f4nt3*@dev-tools.labs.gmv.com/nexus/repository/public_pypi/simple

[install]
find-links = https://shared:g4LL1f4nt3*@dev-tools.labs.gmv.com/nexus/repository/public_pypi/simple
' > ~/.config/pip/pip.conf

exit 0
else
echo '' > ~/.config/pip/pip.conf
exit
fi