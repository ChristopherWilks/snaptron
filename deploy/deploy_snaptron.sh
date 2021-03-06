#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)
#1: Snaptron name of compilation (e.g. srav2)
#2: [optional] directory where data already is (pre built or downloaded)
#./deploy/deploy_snaptron.sh srav2 /snaptron_data

#get the path to this script
#scripts=`perl -e '$f="'${0}'"; $f=~s/\/[^\/]+$/\//; print "$f\n";'`
scripts=$(dirname $0)

#compilation e.g. "tcga"
comp=$1

#installs python & PyLucene specific depdendencies
if [ ! -e ./FINISHED_DEPENDENCIES ]; then
	/bin/bash -x ${scripts}/install_dependencies.sh
elif [ -e ./python/bin/activate ]; then
    source ./python/bin/activate
fi

#pull down the binaries for helper utilities
wget http://snaptron.cs.jhu.edu/data/calc
chmod a+x calc
wget http://snaptron.cs.jhu.edu/data/bgzip_zstd
chmod a+x bgzip_zstd
wget http://snaptron.cs.jhu.edu/data/tabix_zstd
chmod a+x tabix_zstd

DATA_DIR=${2}
if [ -z ${DATA_DIR} ]; then
    DATA_DIR=`pwd`/downloaded_data
    #echo "+++Downloading snaptron data, this make take a while..."
    if [ ! -e $DATA_DIR ]; then
        mkdir $DATA_DIR
    fi
fi

#assume we need to get the data in any case
/bin/bash -x ${scripts}/download_compilation_data.sh $comp $DATA_DIR

#link the right configs for this compilation
/bin/bash -x ${scripts}/configure_compilation_and_data.sh $comp $DATA_DIR

#setup directory for registry (only for this compilation though)
#assumes full path in $DATA_DIR
if [[ "$comp" == "test_gtex" ]] ; then
    mkdir -p ../test/compilations/${comp}_snaptron/
    ln -fs ${DATA_DIR}/lucene_indexed_numeric_types.tsv ../test/compilations/${comp}_snaptron/
else
    mkdir -p compilations/${comp}_snaptron/
    ln -fs ${DATA_DIR}/lucene_indexed_numeric_types.tsv compilations/${comp}_snaptron/
fi
