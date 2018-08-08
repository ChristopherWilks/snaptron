#!/bin/bash

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`

echo "+++Linking config files for ${1} compilation"
#link config file(s)
${scripts}/setup_configs.sh ${1}

#link up data directory if provided
if [ ! -z "${2}" ]; then
	echo "linking provided data directory"
	ln -fs ${2} ./data
	ln -fs data/lucene_indexed_numeric_types.tsv
fi

