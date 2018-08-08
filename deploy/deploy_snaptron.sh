#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)
#1: Snaptron name of compilation (e.g. srav2)
#2: [optional] directory where data already is (pre built or downloaded)
#./deploy/deploy_snaptron.sh srav2 /snaptron_data

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`

#installs python & PyLucene specific depdendencies
if [ ! -e ./FINISHED_DEPENDENCIES ]; then
	/bin/bash -x ${scripts}/install_dependencies.sh
fi

DATA_DIR=${2}
if [ -z ${DATA_DIR} ]; then
    #echo "+++Downloading snaptron data, this make take a while..."
    if [ ! -e ./downloaded_data ]; then
        mkdir ./downloaded_data
    fi
    DATA_DIR=./downloaded_data
    /bin/bash -x ${scripts}/download_compilation_data.sh $1 $DATA_DIR
fi

#link the right configs for this compilation
/bin/bash -x ${scripts}/configure_compilation_and_data.sh $1 $DATA_DIR
