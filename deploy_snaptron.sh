#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)

#Tabix >= 1.2.1 and Sqlite3 >= 3.11.0 need to be compiled and already in the PATH *before*
#running this script

#To use the uncompressed version of Tabix, pass a "1" into this
#script following the compilation name, e.g.:

#./deploy_snaptron.sh srav2 1

#our modified version of bgzip must also be present in the PATH
#before any other bgzip binaries
#get it here:
#http://snaptron.cs.jhu.edu/data/htslib-1.2.1_nocomp.tar.gz

echo "+++Setting up Python for Snaptron for ${1} compilation"
#setup python for Snaptron
#from https://virtualenv.pypa.io/en/stable/installation/
curl -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-13.1.2.tar.gz
tar xvfz virtualenv-13.1.2.tar.gz
cd virtualenv-13.1.2
python virtualenv.py ../python
cd ..
source ./python/bin/activate
pip install -r requirements.txt

echo "+++Setting up PyLucene and dependencies (this requires sudo)"
#this requires additional packages at the system level
./install_pylucene.sh

echo "+++Linking config files for ${1} compilation"
#link config file(s)
./setup_configs.sh ${1}

#grab data
mkdir data
cd data
#echo "+++Downloading snaptron data, this make take a while..."
wget http://snaptron.cs.jhu.edu/data/${1}/samples.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/junctions.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/all_transcripts.gtf.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/refseq_transcripts_by_hgvs.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/ucsc_known_canonical_transcript.tsv

echo "+++Creating Tabix index on transcripts file"
#creation of Tabix index of all_transcripts
tabix -s 1 -b 4 -e 5 all_transcripts.gtf.bgz

echo "+++Creating SQLite DB of junctions"
#creation of sqlite junction db
../scripts/build_sqlite_junction_db.sh junctions junctions.bgz

echo "+++Creating Lucene indices"
#run lucene indexer on metadata
cat samples.tsv | perl ../scripts/infer_sample_metadata_field_types.pl > samples.tsv.type_inference
cat samples.tsv | python ../lucene_indexer.py samples.tsv.type_inference > run_indexer 2>&1

echo "+++Creating Tabix index on junctions file"
if [ -z ${2+v} ]; then
        echo "sticking with compressed junctions file"
        ln -s junctions.bgz junctions_uncompressed.bgz
else
#The compress_level=0 modified bgzf must be in your path before any standard bgzf binaries
        echo "creating uncompressed junctions file"
        zcat junctions.bgz | bgzip > junctions_uncompressed.bgz
fi

tabix -s 2 -b 3 -e 4 junctions_uncompressed.bgz

cd ../
ln -s data/lucene_indexed_numeric_types.tsv
