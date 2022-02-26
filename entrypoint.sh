#!/usr/bin/env bash
set -x

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
   /bin/bash -x ${DEPLOY_DIR}/${compilation}/deploy/deploy_snaptron.sh ${compilation}
# case 2): run (assume everything's already setup)
elif [ "$1" == "run" ] ; then
   ln -fs /${DEPLOY_DIR}/${compilation}/instances/proxy.conf /etc/apache2/mods-available/
   ln -fs /etc/apache2/mods-available/proxy.conf /etc/apache2/mods-enabled/
   ln -fs ../mods-available/proxy.load /etc/apache2/mods-enabled/
   ln -fs ../mods-available/slotmem_shm.load /etc/apache2/mods-enabled/
   ln -fs ../mods-available/proxy_balancer.conf /etc/apache2/mods-enabled/
   ln -fs ../mods-available/proxy_balancer.load /etc/apache2/mods-enabled/
   ln -fs ../mods-available/lbmethod_byrequests.load /etc/apache2/mods-enabled/
   ln -fs ../mods-available/proxy_http.load /etc/apache2/mods-enabled/
   /etc/init.d/apache2 start
   server_exec=$(ls /${DEPLOY_DIR}/${compilation}/*_snaptron_server)
   cd /${DEPLOY_DIR}/${compilation} && python $server_exec --no-daemon
else
   echo "Did not understand command: \"$*\""
fi
