#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)
#1: Snaptron name of compilation (e.g. srav2)
#2 (optional): 1 if we should generate the uncompressed version of the junctions database (for performance)

#./deploy/deploy_snaptron.sh srav2 1

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`

#installs python & PyLucene specific depdendencies
if [ -z ./FINISHED_DEPENDENCIES ]; then
	/bin/bash -x ${script}/install_dependencies.sh
fi

#echo "+++Downloading snaptron data, this make take a while..."
mkdir ./data
/bin/bash -x ${scripts}/download_compilation_data.sh $1 $2

#link the right configs for this compilation
/bin/bash -x ${scripts}/configure_compilation_and_data.sh $1
