#!/bin/bash
set -x

#declare -a insts=( "srav1" "srav2" "gtex" "tcga" "test" )
declare -a insts=( "test" )
cd /data/gigatron/
for x in "${insts[@]}"
do
	screen -d -m ./run_snaptron_server.sh ${x}
done
