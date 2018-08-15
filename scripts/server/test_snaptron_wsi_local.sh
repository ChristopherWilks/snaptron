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
	echo "testing $x exons"
	curl "http://${HOST}:${x}/exons?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}:${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
done

#supermouse encode ct_h_s ct_m_s
declare -a insts=( "1585" "1587" "1590" "1591")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}:${x}/snaptron?regions=chr1:1-20854861&rfilter=samples_count:200" 2>/dev/null| head -3 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}:${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x exons"
	curl "http://${HOST}:${x}/exons?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}:${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
done

#abmv1b abmv1a ct_h_b ct_m_b clark
declare -a insts=( "1589" "1588" "1592" "1593" "1594")
for x in "${insts[@]}"
do
	echo "testing $x junctions"
	curl "http://${HOST}:${x}/snaptron?regions=chr1:1-20854861" 2>/dev/null| head -3 | cut -f 1-10
	#test ALK region
	echo "testing $x genes"
	curl "http://${HOST}:${x}/genes?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x exons"
	curl "http://${HOST}:${x}/exons?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
	echo "testing $x bases"
	curl "http://${HOST}:${x}/bases?regions=chr2:29899597-29907199" 2>/dev/null| head -3 | cut -f 1-10
done

#tcga specific to check if Lucene is working, 73
curl "http://snaptron.cs.jhu.edu/tcga/snaptron?regions=chr16:28931939-28933114&sfilter=gdc_cases.project.project_id:TCGA-DLBC" | grep "TCGA:I" | wc -l
#tcga fusions, 47
curl "http://snaptron.cs.jhu.edu:1575/snaptron?regions=chr16:28931939-28933114&sfilter=gdc_cases.project.project_id:TCGA-DLBC" | wc -l

#curl "http://${HOST}/mouseling/snaptron?regions=chr1:1-20854861&rfilter=samples_count:50" 2>/dev/null| grep -i "mouseling:I" | head -1
