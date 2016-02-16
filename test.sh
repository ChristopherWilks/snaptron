#!/bin/bash
source python/bin/activate

python test_snaptron.py
python ./snaptron.py 'regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000' 2> /dev/null | wc -l
curl "http://stingray.cs.jhu.edu:8443/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000" 2> /dev/null | wc -l
curl --data 'fields="[{"intervals":["chr11:82970135-82997450"],"samples_count":[{"op":">:","val":100}],"coverage_sum":[{"op":">:","val":1000}]}]"' http://stingray.cs.jhu.edu:8443/snaptron 2>/dev/null | wc -l
