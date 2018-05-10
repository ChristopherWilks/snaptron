#!/bin/bash

SQLITE3='sqlite3'
BGZIP_COMP='bgzip'
BGZIP_UNCOMP='~/bgzip'

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

$SQLITE3 ${1}.sqlite < ${p}/snaptron_schema.sql

mkfifo ./import
mkfifo ./import2

zcat $2 | sort -k2,2 -k3,3n -k4,4n | tee ./import | tee ./import2 | $BGZIP_COMP > junctions.ordered.bgz &
cat ./import2 | $BGZIP_UNCOMP > junctions_uncompressed.ordered.bgz
$SQLITE3 ${1}.sqlite -cmd '.separator "\t"' ".import ./import intron"
$SQLITE3 ${1}.sqlite < ${p}/snaptron_schema_index.sql

rm ./import
rm ./import2
