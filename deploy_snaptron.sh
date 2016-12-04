#!/bin/bash

#Tabix and Sqlite3 need to be compiled and already in the PATH *before*
#running this script

#grab data
mkdir data
cd data
wget http://snaptron.cs.jhu.edu/data/${1}/samples.tsv ./
wget http://snaptron.cs.jhu.edu/data/${1}/junctions.bgz ./
wget http://snaptron.cs.jhu.edu/data/${1}/all_transcripts.gtf.bgz ./
wget http://snaptron.cs.jhu.edu/data/${1}/refseq_transcripts_by_hgvs.tsv ./
wget http://snaptron.cs.jhu.edu/data/${1}/ucsc_known_canonical_transcript.tsv ./

#creation of Tabix index of junctions and all_transcripts
tabix -s 2 -b 3 -e 4 junctions.bgz
tabix -s 1 -b 4 -e 5 all_transcripts.gtf.bgz

#creation of sqlite junction db
scripts/build_sqlite_junction_db.sh ${1}_junc junctions.bgz
#creation of sample2junction of sqlite by_sample_id db
scripts/build_sqlite_sample_mapping_db.sh ${1}_sample_ids junctions.bgz

cd ..

#setup python for Snaptron
virtualenv ./python
source ./python/bin/activate
pip install -r dependencies.txt

#link config file(s)
./setup_configs.sh ${1}
