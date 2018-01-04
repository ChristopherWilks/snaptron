#!/bin/bash
#$1 is the path to the snaptron_data directory e.g. /dataB/snaptron_data
#assumes "snaptron" (srav2) has already been cloned and setup as ./snaptron

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

declare -a insts=( "gtex" "tcga" "supermouse" "encode1159" "abmv1a" "abmv1b" )
for x in "${insts[@]}"
do
	echo "setting up $x compilation"
	$p/setup_compilations_from_base_snaptron.sh $x $1/${x}
done
