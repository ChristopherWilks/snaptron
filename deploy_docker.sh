#!/bin/sh
# Deploy the Snaptron server code with compilation-specific configuration + all data/indices 
# necessary to server the specific compilation
# assumes a previously built Snaptron Docker image
# params:
#1: full path to directory where Snaptron code + data files (large) will be persisted
#2: name of compilation to deploy (e.g. clark, tcga, etc...)

# deploy based on a compilation passed in by the user, expects that the build_docker.sh script has already been run
docker run --rm -i -t --name snaptron --volume $1:/deploy:rw snaptron deploy $2
