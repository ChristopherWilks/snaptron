#!/usr/bin/env bash

DEPLOY_DIR="/deploy"

# required to run in any case
[ ! -d "${DEPLOY_DIR}" ] && \
   echo "Must mount Snaptron data directory to ${DEPLOY_DIR} in container" && \
   exit 1
  
# compilation argument needed in both "deploy" and "run" case
compilation=$2
[ -z "${compilation}" ] && \
   echo "Must specify compilation as argument to deploy" && \
   exit 1

# case 1):
# this will download all required compilation-specific data files
# and will either create or download related indices
if [ "$1" == "deploy" ] ; then
   cd ${DEPLOY_DIR}
   if [ ! -e ./${compilation} ]; then
   	git clone https://github.com/ChristopherWilks/snaptron.git ./${compilation}
   fi
   cd ${compilation}
   #assume dependencies have been installed in the container
   touch ./FINISHED_DEPENDENCIES
   /bin/bash -x /snaptron/deploy/deploy_snaptron.sh ${compilation}
# case 2): run (assume everything's already setup)
elif [ "$1" == "run" ] ; then
   cd /deploy/${compilation} && python /deploy/${compilation}/snaptron_server --no-daemon
else
   echo "Did not understand command: \"$*\""
fi
