#!/bin/bash
set -x

declare -a insts=( "srav1" "srav2" "gtex" "tcga" )
for x in "${insts[@]}"
do
	curl "http://snaptron.cs.jhu.edu/${x}/snaptron?regions=CD99&rfilter=samples_count:20" | grep -i "${x}:I" | wc -l
done
