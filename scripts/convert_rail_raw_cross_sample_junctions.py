#!/usr/bin/env python2.7

import sys
import gzip
import argparse

"""
Reformats raw cross sample Rail junctions
into Snaptron compatible format with
all samples collapsed into a comma-delimited
list of sample_id:coverage.
"""

def main():
    parser = argparse.ArgumentParser(description=__doc__, 
            formatter_class=argparse.RawDescriptionHelpFormatter)
    #parser.add_argument('--bowtie-idx', type=str, required=True,
    #    help='path to Bowtie index basename')
    parser.add_argument('--input-file', type=str, required=True,
        help='path to Rail junctions file')
    parser.add_argument('--data-src', type=str, required=False, default="0", 
        help='integer ID identifying the compilation/source')
    args = parser.parse_args()
    samples=[]
    with gzip.open(args.input_file) as f:
        snaptron_id = 0
        for line in f:
            line = line.rstrip()
            fields = line.split("\t")
            if len(samples) == 0:
                samples = fields[1:]
                with open(args.input_file + ".samples2ids","w") as fout:
                    for (idx,s) in enumerate(samples):
                        fout.write(str(idx)+"\t"+str(s)+"\n")
                continue
            (chrom,strand,start,end) = fields[0].split(";")
            jlength = (int(end) - int(start)) + 1
            sample_fields = []
            covs = []
            sum_ = 0
            for (idx,cov) in enumerate(fields[1:]):
                cov = int(cov)
                if cov > 0:
                    sample_fields.append(str(idx)+":"+str(cov))
                    covs.append(cov)
                    sum_ += cov
            covs = sorted(covs)
            count = len(covs)
            median = int(count/2)
            if count % 2 == 0:
                median = round((covs[median-1] + covs[median])/2.0, 3)
            else:
                median = round(covs[median], 3)
            avg = round(sum_/float(count), 3)
            sample_fields = ","+",".join(sample_fields)
            annotated = 0
            annot_l = "0"
            annot_r = "0"
            motif_l = ""
            motif_r = ""
            sys.stdout.write("\t".join([str(x) for x in [snaptron_id,chrom,start,end,jlength,strand,annotated,motif_l,motif_r,annot_l,annot_r,sample_fields,count,sum_,"%.3f"%avg,"%.3f"%median,args.data_src]]) + "\n")
            snaptron_id += 1

        
if __name__ == '__main__':
    main()
    
