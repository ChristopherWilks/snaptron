#!/bin/bash
#set -x

#HOST="162.129.223.10"
#HOST="snaptron.cs.jhu.edu"
HOST="localhost"

declare -a insts=( "srav1m" "srav3h" "gtexv2" "tcgav2")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}/${x}/snaptron?regions=CD99&rfilter=samples_count:20" 2>/dev/null| grep -i "${x}:I" | head -1 | cut -f 1-10
done

declare -a insts=( "srav1" "srav2" "gtex" "tcga")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}/${x}/snaptron?regions=CD99&rfilter=samples_count:20" 2>/dev/null| grep -i "${x}:I" | head -1 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}/${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:G" | head -1 | cut -f 1-10
	echo "testing $x exons"
	curl "http://${HOST}/${x}/exons?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:E" | head -1 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}/${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:B" | head -1 | cut -f 1-10
done


declare -a insts=( "encode1159" "ct_h_s" "ct_m_s", "mesa")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}/${x}/snaptron?regions=chr1:1-20854861&rfilter=samples_count:200" 2>/dev/null| grep -i "${x}:I" | head -1 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}/${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:G" | head -1 | cut -f 1-10
	echo "testing $x exons"
	curl "http://${HOST}/${x}/exons?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:E" | head -1 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}/${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:B" | head -1 | cut -f 1-10
done

declare -a insts=( "abmv1b" "abmv1a" "ct_h_b" "ct_m_b" "clark" "rpc")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}/${x}/snaptron?regions=chr1:1-20854861" 2>/dev/null| grep -i "${x}:I" | head -1 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}/${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:G" | head -1 | cut -f 1-10
	echo "testing $x exons"
	curl "http://${HOST}/${x}/exons?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:E" | head -1 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}/${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| grep -i "${x}:B" | head -1 | cut -f 1-10
done
#curl "http://${HOST}/mouseling/snaptron?regions=chr1:1-20854861&rfilter=samples_count:50" 2>/dev/null| grep -i "mouseling:I" | head -1
