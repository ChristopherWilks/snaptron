#!/usr/bin/env bash
set -o pipefail -o errexit 

export LC_ALL=C

SQLITE3='sqlite3'
BGZIP_COMP='bgzip'
TABIX='tabix'
BGZIP_UNCOMP='~/bgzip'

#e.g. ${dtype}.gz, should be fully formatted already for Snaptron
infile=$1
tmpdir=$2
#junctions,genes, or exons
dtype=$3
#might be undefined
build_uncompressed=$4

scripts=$(dirname $0)

if [[ -e ${dtype}.sqlite ]]; then
    rm ${dtype}.sqlite
fi
$SQLITE3 ${dtype}.sqlite < ${scripts}/snaptron_schema.sql

rm -f ./import ./import2
mkfifo ./import
mkfifo ./import2

zcat $infile | sort -T $tmpdir -k2,2 -k3,3n -k4,4n | tee ./import | tee ./import2 | $BGZIP_COMP > ${dtype}.bgz &
if [[ -v $build_uncompressed ]]; then
    cat ./import2 | $BGZIP_UNCOMP > ${dtype}_uncompressed.bgz &
else
    cat ./import2 > /dev/null &
    ln -fs ${dtype}.bgz ${dtype}_uncompressed.bgz
fi
$SQLITE3 ${dtype}.sqlite -cmd '.separator "\t"' ".import ./import intron"
$SQLITE3 ${dtype}.sqlite < ${scripts}/snaptron_schema_index.sql

tabix -0 -s 2 -b 3 -e 4 ${dtype}.bgz
if [[ -v $build_uncompressed ]]; then
    tabix -0 -s 2 -b 3 -e 4 ${dtype}_uncompressed.bgz
else
    ln -fs ${dtype}.bgz.tbi ${dtype}_uncompressed.bgz.tbi
fi

rm ./import
rm ./import2
