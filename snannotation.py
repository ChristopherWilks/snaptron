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
    params = {'regions':[],'contains':0}
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


def load_gene_coords(filepath):
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
                        if abs(en2-en) <= snapconf.MAX_GENE_PROXIMITY:
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

def gene2coords(geneq):
    gene_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.REFSEQ_ANNOTATION)
    gene_pickle_file = "%s.pkl" % (gene_file)
    gene_map = snaputil.load_cpickle_file(gene_pickle_file)
    if not gene_map:
        gene_map = load_gene_coords(gene_file)
    snaputil.store_cpickle_file(gene_pickle_file,gene_map)
    geneq = geneq.upper()
    if geneq not in gene_map:
        sys.stderr.write("ERROR no gene found by name %s\n" % (geneq))
        sys.exit(-1)
    return sorted(gene_map[geneq].iteritems())


def query_gene_regions(intervalq,contains=False):
    print_header = True
    ra = snaptron.default_region_args._replace(tabix_db_file=snapconf.TABIX_GENE_INTERVAL_DB,range_filters=None,save_introns=False,header=snapconf.GENE_ANNOTATION_HEADER,prefix="Mixed:G",cut_start_col=1,region_start_col=snapconf.GENE_START_COL,region_end_col=snapconf.GENE_END_COL,contains=contains,debug=DEBUG_MODE)
    for interval in intervalq:
        if snapconf.INTERVAL_PATTERN.search(interval):
           (ids,sids) = snaptron.run_tabix(interval,region_args=ra)
        else:
            #if given a gene name, first convert to coordinates and then search tabix
            for (chrom,coord_tuples) in gene2coords(interval):
                for coord_tuple in coord_tuples:
                    (st,en) = coord_tuple
                    (ids_,sids_) = snaptron.run_tabix("%s:%d-%d" % (chrom,st,en),region_args=ra)
                    if ra.print_header:
                        ra=ra._replace(print_header=False)
  
def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    params = process_params(input_)
    query_gene_regions(params['regions'],contains=(int(params['contains'])==1))

if __name__ == '__main__':
    main()
