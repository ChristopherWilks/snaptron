#!/usr/bin/env bash
set -o pipefail -o errexit 

SQLITE3='sqlite3'
BGZIP_COMP='bgzip'
TABIX='tabix'
BGZIP_UNCOMP='~/bgzip'

#e.g. "tcga"
compilation=$1
#e.g. junctions.gz, should be fully formatted already for Snaptron
junctions=$2
#might be undefined
build_uncompressed_junctions=$3

scripts=$(dirname $0)

if [[ -e ${compilation}.sqlite ]]; then
    rm ${compilation}.sqlite
fi
$SQLITE3 ${compilation}.sqlite < ${scripts}/snaptron_schema.sql

mkfifo ./import
mkfifo ./import2

zcat $junctions | sort -k2,2 -k3,3n -k4,4n | tee ./import | tee ./import2 | $BGZIP_COMP > junctions.ordered.bgz &
if [[ -v $build_uncompressed_junctions ]]; then
    cat ./import2 | $BGZIP_UNCOMP > junctions_uncompressed.ordered.bgz &
else
    cat ./import2 > /dev/null &
fi
$SQLITE3 ${compilation}.sqlite -cmd '.separator "\t"' ".import ./import intron"
$SQLITE3 ${compilation}.sqlite < ${scripts}/snaptron_schema_index.sql

tabix -0 -s 2 -b 3 -e 4 junctions.ordered.bgz
if [[ -v $build_uncompressed_junctions ]]; then
    tabix -0 -s 2 -b 3 -e 4 junctions_uncompressed.ordered.bgz
fi

rm ./import
rm ./import2
