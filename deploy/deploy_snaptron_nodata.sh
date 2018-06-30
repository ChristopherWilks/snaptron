#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)
#parameters:
#1: Snaptron name of compilation (e.g. srav2)
#2 (optional): Full path to directory where all data and Snaptron indices have already been stored/created

#Tabix >= 1.2.1 and Sqlite3 >= 3.11.0 need to be compiled and already in the PATH *before*
#running this script

#To use the uncompressed version of Tabix, pass a "1" into this
#script following the compilation name, e.g.:

#./deploy/deploy_snaptron_nodata.sh srav2 /path/to/data

#our modified version of bgzip must also be present in the PATH
#before any other bgzip binaries
#get it here:
#http://snaptron.cs.jhu.edu/data/htslib-1.2.1_nocomp.tar.gz

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`

echo "+++Setting up Python for Snaptron for ${1} compilation"
#setup python for Snaptron
#from https://virtualenv.pypa.io/en/stable/installation/
curl -L -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-13.1.2.tar.gz
tar xvfz virtualenv-13.1.2.tar.gz
cd virtualenv-13.1.2
python virtualenv.py ../python
cd ..
source ./python/bin/activate
pip install -r requirements.txt

echo "+++Setting up PyLucene and dependencies (this requires sudo)"
#this requires additional packages at the system level
${scripts}/install_pylucene.sh

echo "+++Linking config files for ${1} compilation"
#link config file(s)
${scripts}/setup_configs.sh ${1}

#link up data directory if provided
if [ ! -z "${2}" ]; then
	echo "linking provided data directory"
	ln -fs ${2} ./data
	ln -fs data/lucene_indexed_numeric_types.tsv
fi
