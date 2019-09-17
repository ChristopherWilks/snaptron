#!/bin/bash

comp=$1

ln -fs ./snaptron_server ./${comp}_snaptron_server
ln -fs instances/snapconf.py.${comp} ./snapconf.py
if [ $comp = "srav1" ] || [ $comp = "srav2" ] || [ $comp = "test" ]; then
    comp2=$comp
    if [ $comp = "test" ]; then
        comp="srav2"
    fi
	ln -f instances/test_snaptron.py.${comp} ./test_snaptron.py
	ln -fs instances/tests.sh.${comp} ./tests.sh
	ln -fs instances/test_s2i_ids_15.snaptron_ids.${comp} ./test_s2i_ids_15.snaptron_ids
	ln -fs instances/test_annot_full.${comp} ./test_annot_full
	ls instances/*ucsc*.${comp} | perl -ne 'chomp; $s=$_; $s1=$s; $s1=~s/\.srav.$//; $s1=~s/instances\///; `ln -fs $s $s1`;'
    comp=$comp2
fi
if [ $comp = "srav2" ] || [ $comp = "test" ]; then
    comp="srav2"
	ln -fs instances/test_s2i_ids_3.snaptron_ids.${comp} ./test_s2i_ids_3.snaptron_ids
	ln -fs instances/lucene_range_ids.test.${comp} ./lucene_range_ids.test
fi
