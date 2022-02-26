#!/bin/bash -x
export PORT=1601
export HOST=localhost
export PATH_=''

export LC_ALL=C

curl --data 'groups=Z3JvdXA9cjImcmVnaW9ucz1DRDk5fHx8Z3JvdXA9cjMmY29udGFpbnM9MSZyZWdpb25zPWNocjI6Mjk0NDYzOTUtMzAxNDI4NTgmcmZpbHRlcj1zYW1wbGVzX2NvdW50PjoxMDAmcmZpbHRlcj1hbm5vdGF0ZWQ6MQ==' http://$HOST:$PORT/$PATH_/snaptron >test.out.1
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=ALK&rfilter=coverage_avg>:6&sfilter=rail_id:47852" >test.out.2
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr2:29192774-29921611&rfilter=coverage_avg>:6&sfilter=rail_id:47852" >test.out.3
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000" 2> /dev/null >test.out.4
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000&fields=snaptron_id" 2> /dev/null >test.out.5.sids
curl --data 'fields=[{"intervals":["chr11:82970135-82997450"],"samples_count":[{"op":">:","val":100}],"coverage_sum":[{"op":">:","val":1000}]}]' http://$HOST:$PORT/$PATH_/snaptron 2>/dev/null >test.out.6
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=description:cortex" 2>/dev/null >test.out.7.samples
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=all:BONE%20METASTATIC%20tumor" 2>/dev/null >test.out.8.samples
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=run_accession:DRR001622" 2>/dev/null >test.out.9.samples
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=all:tissue" 2>/dev/null >test.out.10.samples
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=spots<:100" 2>/dev/null >test.out.11.samples
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000&sfilter=description:cortex" 2>/dev/null >test.out.12
curl "http://$HOST:$PORT/$PATH_/samples?sfilter=description:cortex" 2>/dev/null >test.out.13.samples
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:7&rfilter=coverage_sum>:10&sfilter=description:cortex" 2>/dev/null >test.out.14
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:7&rfilter=coverage_sum>:10&sids=31219,2799,15180,27751,711,25730,24689,39848,268,43885,27320,28894,45197,29354,18194,5345,35385,34319,2309,42350,22857,34835,33340,26346,2230,15834,38870,22314,31852,31352,21294" 2>/dev/null >test.out.15
curl "http://$HOST:$PORT/$PATH_/samples?ids=0,4,10" 2>/dev/null >test.out.16.samples
curl "http://$HOST:$PORT/$PATH_/samples/4" 2>/dev/null >test.out.17.samples
curl "http://$HOST:$PORT/$PATH_/snaptron?ids=33401865,33401867,33401868" 2>/dev/null >test.out.18
curl --data 'fields=[{"ids":["33401865","33401867","33401868"]}]' http://$HOST:$PORT/$PATH_/snaptron 2>/dev/null >test.out.19
curl "http://$HOST:$PORT/$PATH_/snaptron/33401865" 2>/dev/null >test.out.20
curl --data 'fields=[{"ids":["0","5","11"]}]' http://$HOST:$PORT/$PATH_/samples 2>/dev/null >test.out.21.samples
curl --data 'fields=[{"ids":["0","5","11"],"sample_fields":"0,1,11"}]' http://$HOST:$PORT/$PATH_/samples 2>/dev/null >test.out.22.samples
curl "http://$HOST:$PORT/$PATH_/annotations?regions=CD99" 2>/dev/null >test.out.23.annotations
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=chr11:82970135-82997450&rfilter=samples_count>:100&rfilter=coverage_sum>:1000">test.out.24
curl "http://$HOST:$PORT/$PATH_/snaptron?ids=33401865,33401867,33401868&coordinate_string=chr6:9838875-10284241">test.out.26
curl --data 'fields=[{"ids":["14075847"],"intervals":["chr11:82970135-82997450"],"samples_count":[{"op":">:","val":"100"}],"coverage_sum":[{"op":">:","val":"1000"}]}]' http://$HOST:$PORT/$PATH_/snaptron 2>/dev/null | fgrep -v "datatypes" >test.out.29
curl --data 'fields=[{"ids":["7465808"],"intervals":["chr11:82970135-82997450"],"samples_count":[{"op":">:","val":"100"}],"coverage_sum":[{"op":">:","val":"1000"}]},{"ids":["33401865","33401867","33401868"]}]' http://$HOST:$PORT/$PATH_/snaptron 2>/dev/null | fgrep -v "datatypes" >test.out.30
curl "http://$HOST:$PORT/$PATH_/snaptron?contains=1&regions=chr2:29446395-30142858&rfilter=samples_count>:100&rfilter=annotated:1" 2>/dev/null>test.out.31
curl "http://$HOST:$PORT/$PATH_/genes?regions=ALK&sids=40099,40100">test.out.32.genes
curl "http://$HOST:$PORT/$PATH_/genes?regions=ENSG00000171094.15" >test.out.33.genes
curl --data-urlencode groups@bulk_test_large_samples.txt.2.b64 http://$HOST:$PORT/$PATH_/snaptron >test.out.34
curl --data-urlencode groups@jons_breaking_bulk_query.b64 http://$HOST:$PORT//snaptron >test.out.35
curl "http://$HOST:$PORT/$PATH_/snaptron?regions=SF3B1&sids=SRP063493&rfilter=annotated:0&rfilter=left_annotated:0&rfilter=right_annotated:0&rfilter=strand:-">test.out.36
REGION='chr11:82970135-82997450'
curl -s "http://$HOST:$PORT/$PATH_/bases?regions=${REGION}&header=0" >test.out.37.bases
curl -s "http://$HOST:$PORT/$PATH_/bases?regions=${REGION}&label=bob&calc=1&calc_axis=1&calc_op=mean">test.out.38.bases
curl -s "http://$HOST:$PORT/$PATH_/bases?regions=${REGION}&header=0" >test.out.39.bases
curl -s "http://$HOST:$PORT/$PATH_/bases?regions=${REGION}&label=bob&calc=1&calc_axis=0&calc_op=sum">test.out.40.bases
curl "http://$HOST:1557/bases?regions=chrM:1-3" 2>/dev/null >test.out.41.bases

curl 'http://localhost:1601//snaptron?ids=14071379,14071408,14073045,14073543,14073546,14074835,14074841,14074851,14074936,14074988,14075006,14075109,14075114,14075256,14075274,14075276,14075538,14075564,14075776,14075782,14075804,14075805,14075843,14075847' > test.out.5

#junctions
#ls | fgrep "test.out" | egrep -v -e '(samples)|(annotations)|(genes)|(bases)|(sids)' | perl -ne 'BEGIN { `echo -n "" > all.jxs`; } chomp; $f=$_; `tail -n+2 $f | fgrep -v "datatypes" | cut -f 2- >> all.jxs`;'

ls | fgrep "test.out" | egrep -v -e '(samples)|(annotations)|(genes)|(bases)|(sids)' | perl -ne 'BEGIN { `echo -n "" > jx.ids`; } chomp; $f=$_; system("tail -n+2 $f | fgrep -v datatypes | cut -f 2 >> jx.ids");'
all_sids=`cat jx.ids | tr \\\n ","`0
curl "http://localhost:1601//snaptron?ids=$all_sids&header=0" | cut -f 2- | sort -k2,2 -k3,3n -k4,4n | uniq > all.jxs.sorted

#genes
ls | fgrep "test.out" | egrep -e 'genes' | perl -ne 'BEGIN { `echo -n "" > gene.ids`; } chomp; $f=$_; system("tail -n+2 $f | fgrep -v datatypes | cut -f 2 >> gene.ids");'
all_sids=`cat gene.ids | tr \\\n ","`0
curl "http://localhost:1601//genes?ids=$all_sids&header=0" | cut -f 2- | sort -k2,2 -k3,3n -k4,4n | uniq > all.genes.sorted

#bases
cut -f 2- test.out.37.bases test.out.39.bases <(tail -n+2 test.out.41.bases) | sort -k1,1 -k2,2n -k3,3n | uniq > all.bases.sorted
