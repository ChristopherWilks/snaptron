#!/usr/bin/env bash
set -x

DEPLOY_DIR="/deploy"
compilation=test

#symlinks needed to get the proxy module setup in Apache2
ln -fs /${DEPLOY_DIR}/${compilation}/instances/proxy.conf /etc/apache2/mods-available/
ln -fs /etc/apache2/mods-available/proxy.conf /etc/apache2/mods-enabled/
ln -fs ../mods-available/proxy.load /etc/apache2/mods-enabled/
ln -fs ../mods-available/slotmem_shm.load /etc/apache2/mods-enabled/
ln -fs ../mods-available/proxy_balancer.conf /etc/apache2/mods-enabled/
ln -fs ../mods-available/proxy_balancer.load /etc/apache2/mods-enabled/
ln -fs ../mods-available/lbmethod_byrequests.load /etc/apache2/mods-enabled/
ln -fs ../mods-available/proxy_http.load /etc/apache2/mods-enabled/
/etc/init.d/apache2 start
cd /${DEPLOY_DIR}/${compilation} && python /${DEPLOY_DIR}/${compilation}/snaptron_server --no-daemon
