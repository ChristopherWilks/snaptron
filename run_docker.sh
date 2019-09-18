#!/bin/bash
# Run previously built Snaptron Docker image as a container
# assumes the passed compilation has already had it's configuration and data deployed via deploy_docker.sh
# params:
#1: full path to directory where Snaptron code + data files have already been persisted
#2: name of compilation to deploy (e.g. clark, tcga, etc...)

# get the TCP port for the compilation
port=`grep "PORT=" instances/snapconf.py.${2} | cut -d'=' -f 2`

docker run --rm -p 2${port}:${port} -p 2080:80 -i -t --name snaptron --volume $1:/deploy:rw snaptron run $2
