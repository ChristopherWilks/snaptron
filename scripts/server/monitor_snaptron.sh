#!/bin/bash
set -x

declare -a insts=( "srav1" "srav2" "gtex" "tcga" "encode1159" )
echo 6 > srav1.expected
echo 27 > srav2.expected
echo 20 > gtex.expected
echo 16 > tcga.expected
echo 2 > encode1159.expected
for x in "${insts[@]}"
do
	curl "http://snaptron.cs.jhu.edu/${x}/snaptron?regions=CD99&rfilter=samples_count>:50&rfilter=samples_count<:60" | grep -i "${x}:I" | grep "chrX" | wc -l > ${x}.test
	diff ${x}.expected ${x}.test > ${x}.test_result
done

echo 14 > supermouse.expected
curl 'http://snaptron.cs.jhu.edu/supermouse/snaptron?regions=chrX:9000000-9986868&rfilter=samples_count>:50&rfilter=samples_count<:60' | grep -i "supermouse:I" | grep "chrX" | wc -l > supermouse.test
diff supermouse.expected supermouse.test > supermouse.test_result

wc -l *.test_result | perl -ne 'chomp; ($diff,$compilation)=split(/\s+/,$_); next if($compilation eq "total"); if($diff != 0) { `mail -s "Snaptron Compilation $compilation returned unexpected results: 0 != $diff" broadsword@gmail.com`; }
