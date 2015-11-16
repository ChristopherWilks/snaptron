#!/usr/bin/env python

import sys
import os
import subprocess
import re
import shlex
from collections import namedtuple
import urllib2
import operator

operators={'>=':operator.ge,'<=':operator.le,'>':operator.gt,'<':operator.lt,'=':operator.eq,'!=':operator.ne}

TABIX="tabix"
TABIX_INTERVAL_DB='all_SRA_introns_ids_stats.tsv.gz'
TABIX_DB_PATH='/data2/gigatron2'
TABIX_DBS={'chromosome':TABIX_INTERVAL_DB,'samples_count':'sample_count.gz','coverage_sum':'by_coverage_sum.gz','coverage_avg':'by_coverage_avg.gz','coverage_median':'by_coverage_median.gz'}
SAMPLE_MD_FILE='/data2/gigatron2/all_illumina_sra_for_human_ids.tsv'
SAMPLE_IDS_COL=7
INTRON_ID_COL=0

INTRON_URL='http://localhost:8090/solr/gigatron/select?q='
SAMPLE_URL='http://localhost:8090/solr/sra_samples/select?q='

INTRON_HEADER='gigatron_id,chromosome,start,end,strand,donor,acceptor,samples,read_coverage_by_sample,samples_count,coverage_count,coverage_sum,coverage_avg,coverage_median'
SAMPLE_HEADER=""
INTRON_HEADER_FIELDS=INTRON_HEADER.split(",")
INTRON_HEADER_FIELDS_MAP={}
i=0
for field in INTRON_HEADER_FIELDS:
   INTRON_HEADER_FIELDS_MAP[field]=i 
   i+=1


def run_tabix(qargs,rquerys,tabix_db,filter_set=None,sample_set=None,filtering=False):
    tabix_db = "%s/%s" % (TABIX_DB_PATH,tabix_db)
    sys.stderr.write("running %s %s %s\n" % (TABIX,tabix_db,qargs))
    if not filtering:
        sys.stdout.write("Type\t%s\n" % (INTRON_HEADER))
    ids_found=set()
    tabixp = subprocess.Popen("%s %s %s" % (TABIX,tabix_db,qargs),stdout=subprocess.PIPE,shell=True)
    for line in tabixp.stdout:
        fields=[]
        #build either filter set or sample set or both
        if sample_set != None or filter_set != None:
             fields=line.rstrip().split("\t")
             if filter_set != None and fields[INTRON_ID_COL] not in filter_set:
                 continue
             if filtering:
                 ids_found.add(fields[INTRON_ID_COL])
                 continue
             if sample_set != None:
                 sample_ids=set(fields[SAMPLE_IDS_COL].split(","))
                 sample_set.update(sample_ids)
        #filter return stream based on range queries (if any)
        if rquerys:
            if len(fields) == 0:
                fields=line.rstrip().split("\t")
            skip=False
            for rfield in rquerys.keys():
                (op,val)=rquerys[rfield]
                if rfield not in INTRON_HEADER_FIELDS_MAP:
                    sys.stderr.write("bad field %s in range query,exiting\n" % (rfield))
                    sys.exit(-1)
                fidx = INTRON_HEADER_FIELDS_MAP[rfield]
                if not op(float(fields[fidx]),val):
                    skip=True
                    break
            if skip:
                continue
        #now just stream back the result
        if not filtering:
            sys.stdout.write("I\t%s" % (line))
    exitc=tabixp.wait() 
    if exitc != 0:
        raise RuntimeError("%s %s %s returned non-0 exit code\n" % (TABIX,TABIX_DB,args))
    if filtering:
        return ids_found

def stream_samples(sample_set,sample_map):
    sys.stdout.write("Type\t%s\n" % (SAMPLE_HEADER))
    for sample_id in sample_set:
        sys.stdout.write("S\t%s\n" % (sample_map[sample_id]))

#use to load samples metadata to be returned
#ONLY when the user requests by overlap coords OR
#coords and/or non-sample metadata thresholds (e.g. coverage)
#otherwise we'll return the whole thing from SOLR instead
def load_sample_metadata(file_):
    fmd={}
    #dont need the hash-on-column headers just yet
    with open(file_) as f:
       for line in f:
           fields=line.rstrip().split("\t")
           fmd[fields[0]]=line
    return fmd

import urllib
MAX_SOLR_ROWS=1000000000
def stream_solr(solr_query,filter_set=None,sample_set=None):
    header_just_id='gigatron_id_i'
    header_just_id_samples='gigatron_id_i,samples_t'
    #headerF=header.split(',')
    header=INTRON_HEADER
    if not filter_set:
        header=header_just_id_samples
    if not filter_set and not sample_set:
        header=header_just_id
    solr_url = "%s%s&wt=csv&csv.separator=%%09&rows=%d&fl=%s" % (INTRON_URL,urllib.quote_plus(solr_query),MAX_SOLR_ROWS,header)
    sys.stderr.write("opening %s\n" % (solr_url))
    #sys.stderr.write("opening %s%s&wt=csv&fl=gigatron_id_i,chromosome_s,start_i,end_i,strand_s,donor_s,acceptor_s,samples_t,read_coverage_by_sample_t,samples_count_i,coverage_count_i,coverage_sum_i,coverage_avg_d,coverage_median_d&csv.separator=%%09&rows=100000000\n" % ((INTRON_URL,urllib.quote_plus(solr_query))))
    #solrR = urllib2.urlopen("%s%s&wt=csv&fl=gigatron_id_i,chromosome_s,start_i,end_i,strand_s,donor_s,acceptor_s,samples_t&csv.separator=%%09" % (INTRON_URL,urllib.quote_plus(solr_query)))
    #solrR = urllib2.urlopen("%s%s&wt=csv&fl=gigatron_id_i,chromosome_s,start_i,end_i,strand_s,donor_s,acceptor_s,samples_t,read_coverage_by_sample_t,samples_count_i,coverage_count_i,coverage_sum_i,coverage_avg_d,coverage_median_d&csv.separator=%%09&rows=100000000\n" % ((INTRON_URL,urllib.quote_plus(solr_query))))
    solrR = urllib2.urlopen(solr_url)
    line=solrR.readline()
    sys.stderr.write("streaming solr results now (querying done)\n")
    ids_found=set()
    while(line):
        line=line.rstrip()
        fields=line.split("\t")
        if filter_set != None and fields[INTRON_ID_COL] not in filter_set:
            line=solrR.readline()
            continue
        if sample_set != None:
            #fields[SAMPLE_IDS_COL]=fields[SAMPLE_IDS_COL].replace(r'"',r'')
            #sample_ids=set(fields[SAMPLE_IDS_COL].split(','))
            fields[1]=fields[1].replace(r'"',r'')
            sample_ids=set(fields[1].split(','))
            sample_set.update(sample_ids)
        if filter_set == None:
            ids_found.add(fields[0])
        #sys.stdout.write("I\t%s\n" % (line))
        line=solrR.readline()
    if filter_set == None:
        return ids_found

comp_op_pattern=re.compile(r'([=><!]+)')
def range_query_parser(rangeq):
    rquery={}
    if rangeq is None or len(rangeq) < 1:
        return (None,None,rquery)
    fields = rangeq.split(',')
    (first_tdb,first_rquery)=(None,None) #first_col,first_val1,first_val2)
    #for (field_,tdb) in TABIX_DBS.iteritems():
    for field in fields:
        m=comp_op_pattern.search(field)
        (col,op_,val)=re.split(comp_op_pattern,field)
        val=float(val)
        if not m or not col or col not in TABIX_DBS:
            continue
        op=m.group(1)
        if op not in operators:
            sys.stderr.write("bad operator %s in range query,exiting\n" % (str(op)))
            sys.exit(-1)
        rquery[col]=(operators[op],val)
        if first_tdb:
            continue 
        #only do the following for the first range query
        tdb=TABIX_DBS[col]
        first_tdb=tdb
        extension=""
        if op == '=':
            extension="-%d" % (val)
        if op == '<=':
            extension="-%d" % (val)
            val=1
        if op == '<':
            extension="-%d" % (val-1)
            val=1
        if op == '>':
            val=val+1
        first_rquery="1:%d%s" % (val,extension)
    return (first_tdb,first_rquery,rquery)

#cases:
#1) just interval (one function call)
#2) interval + range query(s) (one tabix function call + field filter(s))
#3) one or more range queries (one tabix range function call + field filter(s))
#4) interval + sample (2 function calls: 1 solr for sample filter + 1 tabix using sample filter)
#5) sample (1 solr call -> use interval ids to return all intervals)
#6) sample + range query(s) (2 function calls: 1 solr for sample filter + 1 tabix using sample filter + field filter)
def main():
    input_ = sys.argv[1]
    (intervalq,rangeq,sampleq) = input_.split('|')
    samples = load_sample_metadata(SAMPLE_MD_FILE) 
    sys.stderr.write("loaded %d samples metadata\n" % (len(samples)))
    if len(sampleq) >= 1:
       filter_set = stream_solr(sampleq)
       sys.stderr.write("found %d introns in solr\n" % (len(filter_set)))
    #whether or not we use the interval query as a filter set or the whole query
    sample_set=set()
    (first_tdb,first_rquery,rquery) = range_query_parser(rangeq)
    if len(intervalq) >= 1:
        run_tabix(intervalq,rquery,TABIX_INTERVAL_DB,sample_set=sample_set)
    elif len(rangeq) >= 1:
        run_tabix(first_rquery,rquery,first_tdb,sample_set=sample_set)
    sys.stderr.write("found %d samples\n" % (len(sample_set)))
    #stream_samples(sample_set,samples)

if __name__ == '__main__':
    main()
