#!/bin/bash

ln -fs ./snaptron_server ./${1}_snaptron_server
ln -f instances/snapconf.py.${1} ./snapconf.py
ln -f instances/test_snaptron.py.${1} ./test_snaptron.py
ln -fs instances/tests.sh.${1} ./tests.sh
ln -fs instances/test_s2i_ids_15.snaptron_ids.${1} ./test_s2i_ids_15.snaptron_ids
ln -fs instances/test_annot_full.${1} ./test_annot_full
ln -fs lucene_indexer.py.sra instances/lucene_indexer.py.srav1
ln -fs lucene_indexer.py.sra instances/lucene_indexer.py.srav2
ln -fs instances/lucene_indexer.py.${1} ./lucene_indexer.py
