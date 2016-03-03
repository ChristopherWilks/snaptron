#!/bin/bash
source python/bin/activate

python test_snaptron.py

#system tests (roundtrip)
echo "26" > expected_wc
python ./snaptron.py 'regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000' 2> /dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "26" > expected_wc
curl "http://stingray.cs.jhu.edu:8443/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000" 2> /dev/null | wc -l  > test_wc
diff test_wc expected_wc

echo "26" > expected_wc
curl "http://stingray.cs.jhu.edu:8443/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000&fields=snaptron_id" 2> /dev/null | wc -l  > test_wc
diff test_wc expected_wc

echo "27" > expected_wc
curl --data 'fields="[{"intervals":["chr11:82970135-82997450"],"samples_count":[{"op":">:","val":100}],"coverage_sum":[{"op":">:","val":1000}]}]"' http://stingray.cs.jhu.edu:8443/snaptron 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "32" > expected_wc
curl "http://stingray.cs.jhu.edu:8443/samples?sfilter=description:cortex" 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "4" > expected_wc
curl 'http://stingray.cs.jhu.edu:8443/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000&sfilter=description:cortex' 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

echo "5" > expected_wc
curl --data 'fields="[{"snaptron_id":["33401865","33401867","33401868"]}]"' http://stingray.cs.jhu.edu:8443/snaptron 2>/dev/null | wc -l > test_wc
diff test_wc expected_wc

rm test_wc expected_wc

echo "all tests run"

#FP comparison test
#tabix /data2/gigatron2/all_SRA_introns_ids_stats.tsv.new2_w_sourcedb2.gz chr11:82970135-82997450 | perl -ne 'chomp; @f=split(/\t/,$_); $scount=$f[14]; next if($scount < 10 || $scount > 10); $avg=$f[16]; $med=$f[17]; next if($avg <= 2.0); print "$_\n";' | wc -l
