#!/bin/bash

ln -s ./snaptron_server ./${1}_snaptron_server
ln instances/snapconf.py.${1} ./snapconf.py
ln instances/test_snaptron.py.${1} ./test_snaptron.py
ln -s instances/tests.sh.${1} ./tests.sh
ln -s instances/test_s2i_ids_15.snaptron_ids.${1} ./test_s2i_ids_15.snaptron_ids
ln -s instances/test_annot_full.${1} ./test_annot_full
ln -s ../snaptron/python
ln -s ${2} ./data
