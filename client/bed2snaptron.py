#!/usr/bin/env python2.7
import sys

seen = {}
sys.stdout.write("region\teither\tthresholds\tgroup\n")
#assumes input is in start coordinate sorted order
for line in sys.stdin:
    fields = line.rstrip().split('\t')
    #BED format "name" here is genename
    #score not used
    #assumes exon coordinates
    (chrom,start,end,group,score,strand) = fields[:6]
    if group in seen:
        seen[group]+=1
        group = group.replace(" ","_%d " % (seen[group]))
    else:
        seen[group]=1
    #BED offset of 0 to snaptron 1, so we can just use the starts as they are
    sys.stdout.write("%s:%s-%s\t%d\t%s\t%s\n" %(chrom,start,start,2,"strand=%s&samples_count>=1" % (strand),group))
    sys.stdout.write("%s:%d-%d\t%d\t%s\t%s\n" %(chrom,int(end)+1,int(end)+1,1,"strand=%s&samples_count>=1" % (strand),group))
