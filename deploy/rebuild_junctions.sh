#!/usr/bin/env bash
set -o pipefail -o errexit 

export LC_ALL=C

SQLITE3='sqlite3'
BGZIP_COMP='bgzip'
TABIX='tabix'
BGZIP_UNCOMP='~/bgzip'

#e.g. junctions.gz, should be fully formatted already for Snaptron
junctions=$1
tmpdir=$2
#might be undefined
build_uncompressed_junctions=$3

scripts=$(dirname $0)

if [[ -e junctions.sqlite ]]; then
    rm junctions.sqlite
fi
$SQLITE3 junctions.sqlite < ${scripts}/snaptron_schema.sql

mkfifo ./import
mkfifo ./import2

zcat $junctions | sort -T $tmpdir -k2,2 -k3,3n -k4,4n | tee ./import | tee ./import2 | $BGZIP_COMP > junctions.bgz &
if [[ -v $build_uncompressed_junctions ]]; then
    cat ./import2 | $BGZIP_UNCOMP > junctions_uncompressed.bgz &
else
    cat ./import2 > /dev/null &
    ln -s junctions.bgz junctions_uncompressed.bgz
fi
$SQLITE3 junctions.sqlite -cmd '.separator "\t"' ".import ./import intron"
$SQLITE3 junctions.sqlite < ${scripts}/snaptron_schema_index.sql

tabix -0 -s 2 -b 3 -e 4 junctions.bgz
if [[ -v $build_uncompressed_junctions ]]; then
    tabix -0 -s 2 -b 3 -e 4 junctions_uncompressed.bgz
else
    ln -s junctions.bgz.tbi junctions_uncompressed.bgz.tbi
fi

rm ./import
rm ./import2
