#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)

#sqlite3 >= 3.11.0 need to be compiled and already in the PATH *before*
#running this script

#setup python for Snaptron
#from https://virtualenv.pypa.io/en/stable/installation/
curl -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-13.1.2.tar.gz
tar xvfz virtualenv-13.1.2.tar.gz
cd virtualenv-13.1.2
python virtualenv.py ../python
cd ..
source ./python/bin/activate
pip install -r dependencies.txt

#this requires sudo and may need additional
#packages at the system level
./install_pylucene.sh

#link config file(s)
./setup_configs.sh ${1}

#grab data
mkdir data
cd data
wget http://snaptron.cs.jhu.edu/data/${1}/samples.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/junctions.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/all_transcripts.gtf.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/refseq_transcripts_by_hgvs.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/ucsc_known_canonical_transcript.tsv

#creation of junction and transcript sqlite DBs
../scripts/build_sqlite_junction_db.sh junctions junctions.bgz all_transcripts.gtf.bgz

#run lucene indexer on metadata
cat samples.tsv | perl ../scripts/infer_sample_metadata_field_types.pl > samples.tsv.type_inference 
cat samples.tsv | python ../lucene_indexer.py samples.tsv.type_inference > run_indexer 2>&1
