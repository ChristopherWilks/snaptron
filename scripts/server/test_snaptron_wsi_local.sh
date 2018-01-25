#!/bin/bash
#set -x

HOST="localhost"
HOST2="snaptron.cs.jhu.edu"

#srav2 gtex tcga
declare -a insts=( "1556" "1557" "1558")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}:${x}/snaptron?regions=CD99&rfilter=samples_count:20" 2>/dev/null| head -3 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}:${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}:${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
done

#encode supermouse
declare -a insts=( "1587" "1585")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}:${x}/snaptron?regions=chr1:1-20854861&rfilter=samples_count:200" 2>/dev/null| head -3 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}:${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}:${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
done

#abmv1b abmv1a
declare -a insts=( "1589" "1588")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}:${x}/snaptron?regions=chr1:1-20854861" 2>/dev/null| head -3 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}:${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}:${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
done
#curl "http://${HOST}/mouseling/snaptron?regions=chr1:1-20854861&rfilter=samples_count:50" 2>/dev/null| grep -i "mouseling:I" | head -1
