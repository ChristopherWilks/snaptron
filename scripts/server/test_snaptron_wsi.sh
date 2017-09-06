#!/bin/bash
set -x

declare -a insts=( "srav1" "srav2" "gtex" "tcga")
for x in "${insts[@]}"
do
	curl "http://snaptron.cs.jhu.edu/${x}/snaptron?regions=CD99&rfilter=samples_count:20" | grep -i "${x}:I"
done


declare -a insts=( "encode1159" "supermouse" )
for x in "${insts[@]}"
do
	curl "http://snaptron.cs.jhu.edu/${x}/snaptron?regions=chr1:1-20854861&rfilter=samples_count:200" | grep -i "${x}:I"
done

curl "http://snaptron.cs.jhu.edu/mouseling/snaptron?regions=chr1:1-20854861&rfilter=samples_count:50" | grep -i "mouseling:I"
