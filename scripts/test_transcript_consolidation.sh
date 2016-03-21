#!/bin/bash

echo "TEST: # of lines $1 $2"
cut -d' ' -f 4 $1 | sort -u | wc -l > expected_wc
wc -l $2 | cut -d' ' -f 1 > new_wc
diff expected_wc new_wc

echo "TEST: grep for -1 #1 $2"
fgrep -e '-1,' $2

echo "TEST: grep for -1 #2 $2"
fgrep -e '"-1' $2
