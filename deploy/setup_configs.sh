#!/bin/bash

ln -fs ./snaptron_server ./${1}_snaptron_server
ln -fs instances/snapconf.py.${1} ./snapconf.py
if [ $1 = "srav1" ] || [ $1 = "srav2" ] ; then
	ln -f instances/test_snaptron.py.${1} ./test_snaptron.py
	ln -fs instances/tests.sh.${1} ./tests.sh
	ln -fs instances/test_s2i_ids_15.snaptron_ids.${1} ./test_s2i_ids_15.snaptron_ids
	ln -fs instances/test_annot_full.${1} ./test_annot_full
	ls instances/*ucsc*.${1} | perl -ne 'chomp; $s=$_; $s1=$s; $s1=~s/\.srav.$//; $s1=~s/instances\///; `ln -fs $s $s1`;'
fi
if [ $1 = "srav2" ] ; then
	ln -fs instances/test_s2i_ids_3.snaptron_ids.${1} ./test_s2i_ids_3.snaptron_ids
	ln -fs instances/lucene_range_ids.test.${1} ./lucene_range_ids.test
fi
