#!/bin/bash
source python/bin/activate

python test_snaptron.py
python ./snaptron.py 'regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000' 2> /dev/null | wc -l
curl "http://stingray.cs.jhu.edu:8443/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000" 2> /dev/null | wc -l
curl --data 'fields="[{"intervals":["chr11:82970135-82997450"],"samples_count":[{"op":">:","val":100}],"coverage_sum":[{"op":">:","val":1000}]}]"' http://stingray.cs.jhu.edu:8443/snaptron 2>/dev/null | wc -l

#FP comparison test
#tabix /data2/gigatron2/all_SRA_introns_ids_stats.tsv.new2_w_sourcedb2.gz chr11:82970135-82997450 | perl -ne 'chomp; @f=split(/\t/,$_); $scount=$f[14]; next if($scount < 10 || $scount > 10); $avg=$f[16]; $med=$f[17]; next if($avg <= 2.0); print "$_\n";' | wc -l
