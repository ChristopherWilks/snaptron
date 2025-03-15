#!/usr/bin/env bash
set -eo pipefail
#for debugging
#exec &> /srv/hdd1/logs/snaptron-studies.log2
#set -x
dir=$(dirname $0)

read -r request
while /bin/true; do
  read -r header
  [ "$header" == $'\r' ] && break
done

# parse url & path

url="${request#GET }"
url="${url% HTTP/*}"
path="${url%%\?*}"
#the parameters
query="${url#*\?}"
#echo "$query"
#/bin/bash $dir/query.sh "$query" > /srv/hdd1/logs/out0 2>> /srv/hdd1/logs/snaptron-studies.query.log
/bin/bash $dir/query.sh "$query" 2>> /srv/hdd1/logs/snaptron-studies.query.log
#set +x
#echo <(cat /srv/hdd1/logs/out0)
