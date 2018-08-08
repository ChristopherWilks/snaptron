#!/bin/bash

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

sqlite3 ${1}.sqlite < ${p}/snaptron_schema.sql

mkfifo ./import
zcat $2 > ./import  &
sqlite3 ${1}.sqlite -cmd '.separator "\t"' ".import ./import intron"

sqlite3 ${1}.sqlite < ${p}/snaptron_schema_index.sql
rm ./import
