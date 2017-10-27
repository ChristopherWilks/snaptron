#!/bin/bash
#set -x

declare -a insts=( "srav1" "srav2" "gtex" "tcga")
for x in "${insts[@]}"
do
	curl "http://snaptron.cs.jhu.edu/${x}/snaptron?regions=CD99&rfilter=samples_count:20" 2>/dev/null| grep -i "${x}:I" | head -1 | cut -f 1-10
	#test ALK region
	curl "http://snaptron.cs.jhu.edu/${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:G" | head -1 | cut -f 1-10
done


declare -a insts=( "encode1159" "supermouse" )
for x in "${insts[@]}"
do
	curl "http://snaptron.cs.jhu.edu/${x}/snaptron?regions=chr1:1-20854861&rfilter=samples_count:200" 2>/dev/null| grep -i "${x}:I" | head -1 | cut -f 1-10
	#test ALK region
	curl "http://snaptron.cs.jhu.edu/${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:G" | head -1 | cut -f 1-10
done

#curl "http://snaptron.cs.jhu.edu/mouseling/snaptron?regions=chr1:1-20854861&rfilter=samples_count:50" 2>/dev/null| grep -i "mouseling:I" | head -1
