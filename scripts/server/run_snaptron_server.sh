#!/bin/bash

cd ${1}_snaptron
source python/bin/activate
python ./${1}_snaptron_server --no-daemon
