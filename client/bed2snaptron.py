#!/usr/bin/env python2.7
import sys

seen = set()
sys.stdout.write("region\twithin\texact\tthresholds\tgroup\n")
#assumes input is in start coordinate order sorted
for line in sys.stdin:
    fields = line.rstrip().split('\t')
    (chrom,start,end,group) = fields[:4]
    within = '2'
    (coord1,coord2)=(end,end)
    if group in seen:
        within = '1'
        (coord1,coord2)=(start,start)
    seen.add(group)
    sys.stdout.write("%s:%s-%s\t%s\t%s\t%s\t%s\n" %(chrom,coord1,coord2,within,"","",group))
