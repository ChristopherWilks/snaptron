#!/bin/bash
set -x

declare -a insts=( "srav1" "srav2" "gtex" "tcga" "mouseling" "supermouse" "encode1159" )
cd /data/gigatron/
for x in "${insts[@]}"
do
	screen -S ${x} -d -m ./run_snaptron_server.sh ${x}
done
