#!/bin/bash
export PORT=1556
export HOST=localhost
export PATH_=''

source python/bin/activate

if [ -z $1 ] ; then
    python test_snaptron.py
fi

#system tests (roundtrip)
echo "26" > expected_wc
python ./snaptron.py 'regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000' 2> /dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "91" > expected_wc
python ./sdensity.py "regions=chr2:1-100000&bigwig_db=snps1k" 2> /dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "26" > expected_wc
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000" 2> /dev/null | wc -l  > test_wc
diff test_wc expected_wc

echo "26" > expected_wc
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000&fields=snaptron_id" 2> /dev/null | wc -l  > test_wc
diff test_wc expected_wc

echo "27" > expected_wc
curl --data 'fields=[{"intervals":["chr11:82970135-82997450"],"samples_count":[{"op":">:","val":100}],"coverage_sum":[{"op":">:","val":1000}]}]' http://$HOST:$PORT/$PATH_/snaptron 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "32" > expected_wc
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=description:cortex" 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "2" > expected_wc
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=run_accession:DRR001622" 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000&sfilter=description:cortex" 2>/dev/null | cut -f 2 | egrep -v -e 'id' | sort -u > test_15_ids
diff test_s2i_ids_15.snaptron_ids test_15_ids 

echo "4" > expected_wc
curl "http://$HOST:$PORT/$PATH_/samples?ids=0,4,10" 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "5" > expected_wc
curl --data 'fields=[{"ids":["33401865","33401867","33401868"]}]' http://$HOST:$PORT/$PATH_/snaptron 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "4" > expected_wc
curl --data 'fields=[{"ids":["0","5","11"]}]' http://$HOST:$PORT/$PATH_/samples 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

#echo "3" > expected_wc
#curl "http://$HOST:$PORT/$PATH_/analysis?ids_a=4&ids_b=5,6&compute=jir&ratio=cov&order=T:5" 2>/dev/null | wc -l > test_wc
#diff test_wc expected_wc

echo "22" > expected_wc
curl "http://$HOST:$PORT/$PATH_/annotations?regions=CD99" 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "91" > expected_wc
curl "http://$HOST:$PORT/$PATH_/density?regions=chr2:1-100000&bigwig_db=snps1k" 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

curl "http://$HOST:$PORT/$PATH_/snaptron?contains=1&regions=chr2:29446395-30142858&rfilter=samples_count>:100&rfilter=annotated:1" 2>/dev/null > test_annot_full.test
diff test_annot_full.test test_annot_full

rm test_wc expected_wc

echo "all tests run"

#FP comparison test
#tabix /data2/gigatron2/all_SRA_introns_ids_stats.tsv.new2_w_sourcedb2.gz chr11:82970135-82997450 | perl -ne 'chomp; @f=split(/\t/,$_); $scount=$f[14]; next if($scount < 10 || $scount > 10); $avg=$f[16]; $med=$f[17]; next if($avg <= 2.0); print "$_\n";' | wc -l
