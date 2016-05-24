#!/usr/bin/env python2.7
'''
Similar to the main Snaptron service, takes coordinate range or gene name
and returns list of transcript exons
'''

import sys
import os
import subprocess
import json
import time
import operator

import gzip

import snapconf
import snaputil
import snaptron

DEBUG_MODE=False

def process_params(input_):
    params = {'regions':[],'contains':0,'limit':0}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            sys.stderr.write("unknown parameter %s, exiting\n" % param)
            sys.exit(-1)
        if key == 'regions':
            subparams = val.split(',')
            for subparam in subparams:
                params[key].append(subparam)
        elif key == 'contains':
            if val == '1':
                params[key]=int(val)
        else:
            params[key]=val
    return params


class GeneCoords(object):

    def __init__(self):
        gene_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.REFSEQ_ANNOTATION)
        gene_pickle_file = "%s.pkl" % (gene_file)
        self.gene_map = snaputil.load_cpickle_file(gene_pickle_file)
        if not self.gene_map:
            self.gene_map = self.load_gene_coords(gene_file)
        snaputil.store_cpickle_file(gene_pickle_file,self.gene_map)

    def load_gene_coords(self,filepath):
        gene_map = {}
        with open(filepath,"r") as f:
            for line in f:
                fields = line.rstrip().split('\t')
                (gene_name,chrom,st,en) = (fields[0].upper(),fields[2],int(fields[4]),int(fields[5]))
                #UCSC OFFSET
                st += 1
                if not snapconf.CHROM_PATTERN.search(chrom):
                    continue
                if gene_name in gene_map:
                    add_tuple = True
                    if chrom in gene_map[gene_name]:
                        for (idx,gene_tuple) in enumerate(gene_map[gene_name][chrom]):
                            (st2,en2) = gene_tuple
                            if (st2 <= en and en2 >= en) or (st <= en2 and en >= en2) or abs(en2-en) <= snapconf.MAX_GENE_PROXIMITY:
                                add_tuple = False
                                if st < st2:
                                    gene_map[gene_name][chrom][idx][0] = st
                                if en > en2:
                                    gene_map[gene_name][chrom][idx][1] = en
                    #add onto current set of coordinates
                    if add_tuple:
                        if chrom not in gene_map[gene_name]:
                            gene_map[gene_name][chrom]=[]
                        gene_map[gene_name][chrom].append([st,en]) 
                else:
                    gene_map[gene_name]={}
                    gene_map[gene_name][chrom]=[[st,en]]
        return gene_map

    def gene2coords(self,geneq):
        geneq = geneq.upper()
        if geneq not in self.gene_map:
            sys.stderr.write("ERROR no gene found by name %s\n" % (geneq))
            sys.exit(-1)
        return sorted(self.gene_map[geneq].iteritems())

def query_gene_regions(intervalq,contains=False,limit=0):
    print_header = True
    ra = snaptron.default_region_args._replace(tabix_db_file=snapconf.TABIX_GENE_INTERVAL_DB,range_filters=None,save_introns=False,header=snapconf.GENE_ANNOTATION_HEADER,prefix="Mixed:G",cut_start_col=1,region_start_col=snapconf.GENE_START_COL,region_end_col=snapconf.GENE_END_COL,contains=contains,debug=DEBUG_MODE)
    gc = GeneCoords()
    limit_filter = 'perl -ne \'chomp; @f=split(/\\t/,$_); @f1=split(/;/,$f[8]); $boost=0; $boost=100000 if($f1[1]!~/"NA"/); @f2=split(/,/,$f1[2]); $s1=$f1[2]; print "$s1\\n"; $f[5]=(scalar @f2)+$boost; print "".(join("\\t",@f))."\\n";\' | sort -t"	" -k6,6nr'
    sys.stderr.write("limit_filter %s\n" % (limit_filter))
    additional_cmd = ""
    if limit > 0:
        additional_cmd = "%s | head -%d" % (limit_filter,limit)
    for interval in intervalq:
        if snapconf.INTERVAL_PATTERN.search(interval):
           (ids,sids) = snaptron.run_tabix(interval,region_args=ra)
        else:
            intervals = gc.gene2coords(interval)
            sys.stderr.write("# of gene intervals: %d\n" % (len(intervals)))
            #if given a gene name, first convert to coordinates and then search tabix
            for (chrom,coord_tuples) in intervals:
                sys.stderr.write("# of gene intervals in chrom %s: %d\n" % (chrom,len(coord_tuples)))
                for coord_tuple in coord_tuples:
                    (st,en) = coord_tuple
                    (ids_,sids_) = snaptron.run_tabix("%s:%d-%d" % (chrom,st,en),region_args=ra,additional_cmd=additional_cmd)
                    if ra.print_header:
                        ra=ra._replace(print_header=False)
  
def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    params = process_params(input_)
    query_gene_regions(params['regions'],contains=(int(params['contains'])==1),limit=int(params['limit']))

if __name__ == '__main__':
    main()
