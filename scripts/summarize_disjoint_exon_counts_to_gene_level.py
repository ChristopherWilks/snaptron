#!/usr/bin/env python2.7
#script to replace R code to do gene level summary sums
#of BigWig per exon-per sample expression

#args:
#1) counts groupings to batch together exons into their gene groups
#2) consolidated TSV of all samples' exon-level counts in the original exon order (not sorted!)

import sys

def main():
    if len(sys.argv) < 3:
        stderr.write("must pass the count group filename and the raw exon level sums filename as arguments\n")
        sys.exit(-1)

    count_groupsF = sys.argv[1]
    raw_sumsF = sys.argv[2]
   
    cg = []
    with open(count_groupsF,"rb") as fin:
        cgline = fin.read()
        cglines = cgline.split('\n')
        cg = [x.split('\t')[0] for x in cglines]
  
    counts={}
    #don't load whole file as it's large 
    with open(raw_sumsF,"rb") as fin:
        i = 0
        for line in fin:
            fields = line.rstrip().split('\t')
            gene_id = cg[i]
            if gene_id not in counts:
                counts[gene_id] = [0 for _ in range(len(fields)-3)]
            counts[gene_id] = [int(y) + counts[gene_id][x] for (x,y) in enumerate(fields[3:])]
            i=i+1

    #TODO: make this to not be specific to super mouse # of sample Rail IDs (the 732)
    sys.stdout.write("gene_id\t"+"\t".join(map(str,range(0,732)))+"\n")
    for gene in cg:
        if gene in counts:
            sys.stdout.write("%s\t%s\n" % (gene,"\t".join(map(str,counts[gene]))))
            del(counts[gene])
                
if __name__ == '__main__':
    main()
