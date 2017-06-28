#!/bin/bash
#Deploys snaptron for a new compilation (not one of the original 4: srav1,srav2,gtex,tcga)

#Tabix >= 1.2.1 and Sqlite3 >= 3.11.0 need to be compiled and already in the PATH *before*
#running this script

#required arguments (example of a a run on the "supermouse" compilation below):
#1) name of compilation
#2) path to Rail's cross-sample junction call file (junctions.tsv.gz)
#3) path to bowtie index of source genome
#4) path to directory of already downloaded annotation GTFs from UCSC's table browser
#5) new data source ID (check current set of compilations to know which to use)
#6) path to TSV file of sample metadata information with first column as rail_id (integer ID)

#7) [optional] argument to use the uncompressed version of Tabix (pass a 1)

#./deploy_snaptron_generic.sh supermouse ./junctions.tsv.gz /data3/indexes/mm10/genome ./annotations 6 ./samples.tsv 1

#our modified version of bgzip must also be present in the PATH
#before any other bgzip binaries
#get it here:
#http://snaptron.cs.jhu.edu/data/htslib-1.2.1_nocomp.tar.gz

echo "+++Setting up Python for Snaptron for ${1} compilation"
#setup python for Snaptron
#from https://virtualenv.pypa.io/en/stable/installation/
curl -k -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-13.1.2.tar.gz
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
#YOU WILL NEED TO TAILOR THIS FILE TO YOUR COMPILATION's specific settings
ln -fs ./snaptron_server ./${1}_snaptron_server
rsync -av instances/snapconf.py.default instances/snapconf.py.${1}
ln -f instances/snapconf.py.${1} ./snapconf.py

#setup data
mkdir data
rsync -av $6 data/samples.tsv
cd data
../scripts/setup_generic_snaptron_instance.sh $2 $3 $4 $5 $7
#echo "+++Downloading snaptron data, this make take a while..."
wget http://snaptron.cs.jhu.edu/data/srav2/all_transcripts.gtf.bgz
wget http://snaptron.cs.jhu.edu/data/srav2/refseq_transcripts_by_hgvs.tsv
wget http://snaptron.cs.jhu.edu/data/srav2/ucsc_known_canonical_transcript.tsv

echo "+++Creating Tabix index on transcripts file"
#creation of Tabix index of all_transcripts
tabix -s 1 -b 4 -e 5 all_transcripts.gtf.bgz

cd ../
ln -s data/lucene_indexed_numeric_types.tsv
