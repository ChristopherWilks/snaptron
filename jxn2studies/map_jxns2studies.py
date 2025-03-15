#!/usr/bin/env python3
import sys
import copy
from operator import itemgetter, attrgetter
#e.g. cmd line for this script:
#/usr/bin/time -v tabix junctions.bgz chr1 2> run1 | python3 map_jxns2studies.py samples.tissues.tsv.cut | pigz --fast -p4 > chr1.jxns2studies.gz

#~7 samples worth
MAX_SHORT_LIST_LEN=56

#format for this file is (e.g. samples.tissues.tsv.cut for the specific compilation):
#rail_id(of the sample)<TAB>study/tissue/group to map it to:
#207148<TAB>DRP000465
mappingsF=sys.argv[1]
#sid2study_name mapping for compilation
mappings={}
with open(mappingsF,"r") as fin:
    mappings = {m.split('\t')[0]:m.rstrip().split('\t')[1] for m in fin}

counts0 = {study:[0,0,study] for study in mappings.values()}
#assume we're pulling out by chromosome via tabix and fed to this script via pipe:

def map_sid2study(mappings, counts, sample):
    (sid, cov) = sample.split(':')
    study = mappings[sid]
    try:
        counts[study][0] += 1
        counts[study][1] += int(cov)
    except Exception as e:
        counts[study]=[1,int(cov),study]

for line in sys.stdin:
    f = line.rstrip().split('\t')
    jid=f[0]
    (c,s,e,o,total_count,total_cov)=(f[1],f[2],f[3],f[5],int(f[12]),int(f[13]))
    #now get sample and coverage counts per study:
    counts = {}
    if len(f[11]) > MAX_SHORT_LIST_LEN:
        counts = copy.deepcopy(counts0)
    [map_sid2study(mappings, counts, sample) for sample in f[11].split(',')[1:]]
    #sort by sample counts, then by coverage
    samples_sorted = sorted(counts.values(), key=itemgetter(1), reverse=True)
    samples_sorted2 = sorted(samples_sorted, key=itemgetter(0), reverse=True)
    s0 = [":".join([v[2],str(int(100*(v[0]/total_count))),str(int(100*(v[1]/total_cov)))]) for v in samples_sorted2 if int(100*(v[0]/total_count)) > 0]
    #s0 = [":".join([v[2],"%.0f" % (100*(v[0]/float(total_count))),"%.0f" % (100*(v[1]/float(total_cov)))]) for v in samples_sorted2]
    print("\t".join(["1",jid,c,s,e,o,str(total_count),str(total_cov),",".join(s0)]))
