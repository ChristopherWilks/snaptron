#!/usr/bin/env python2.7
'''
Takes coordinate range or gene name to determine a region to "slice"
out of a requested BigWig file and return in wig (text) format
'''

import sys
import os
import subprocess
import snapconf
import snannotation

bigwig_dir = snapconf.TABIX_DB_PATH
bigwig_dbs = {'snps':"%s/%s" % (bigwig_dir,'snpdensity_hg19_by100b.bw'),'snps1k':"%s/%s" % (bigwig_dir,'snpdensity_hg19_byKB.bw')}

def process_params(input_):
    params = {'regions':[],'bigwig_db':None}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            sys.stderr.write("unknown parameter %s, exiting\n" % key)
            sys.exit(-1)
        elif key == 'regions':
            params[key].append(val)
        else:
            params[key]=val
    return params

def stream_bigwig_range(interval,bigwig_db,print_header):
    m = snapconf.TABIX_PATTERN.search(interval)
    chrom = m.group(1)
    start = m.group(2)
    end = m.group(3)
    bwp = subprocess.Popen("%s -chrom=%s -start=%s -end=%s %s /dev/stdout" % (snapconf.BIGWIG2WIG,chrom,start,end,bigwig_db),stdout=subprocess.PIPE,shell=True)
    for line in bwp.stdout:
      sys.stdout.write(line)
    exitc=bwp.wait() 
    if exitc != 0:
        raise RuntimeError("%s %s %s returned non-0 exit code\n" % (snapconf.BIGWIG2WIG,bigwig_db,interval))
    return (set(),set())

def query_density_regions(intervalq,bigwig_db_name,print_header=True):
    print_header = True
    try:
        bigwig_db = bigwig_dbs[bigwig_db_name]
    except KeyError, e:
        sys.stderr.write("unknown bigWig db name: %s; exiting\n" % (bigwig_db_name))
        exit(-1)
    #ra = snaptron.default_region_args._replace(tabix_db_file=snapconf.TABIX_GENE_INTERVAL_DB,range_filters=None,save_introns=False,header=snapconf.GENE_ANNOTATION_HEADER,prefix="Mixed:G",cut_start_col=1,region_start_col=snapconf.GENE_START_COL,region_end_col=snapconf.GENE_END_COL,contains=contains,debug=DEBUG_MODE)
    #need to use wigtools to slice out region
    gc = snannotation.GeneCoords()
    for interval in intervalq:
        if snapconf.INTERVAL_PATTERN.search(interval):
           (ids,sids) = stream_bigwig_range(interval,bigwig_db,print_header)
        else:
            #if given a gene name, first convert to coordinates and then search tabix
            for (chrom,coord_tuples) in gc.gene2coords(interval):
                for coord_tuple in coord_tuples:
                    (st,en) = coord_tuple
                    (ids_,sids_) = stream_bigwig_range("%s:%d-%d" % (chrom,st,en),bigwig_db,print_header)
                    if print_header:
                      print_header = False


def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    params = process_params(input_)
    query_density_regions(params['regions'],params['bigwig_db'])


if __name__ == '__main__':
    main()
