#!/usr/bin/env python

import sys
import os
import subprocess
import re
import shlex
from collections import namedtuple
import urllib2

TABIX="tabix"
TABIX_DB='/data2/gigatron2/all_SRA_introns_ids_stats.tsv.gz'
SAMPLE_MD_FILE='/data2/gigatron2/all_illumina_sra_for_human_ids.tsv'
SAMPLE_IDS_COL=7
INTRON_ID_COL=0

INTRON_URL='http://localhost:8090/solr/gigatron/select?q='
SAMPLE_URL='http://localhost:8090/solr/sra_samples/select?q='

INTRON_HEADER='gigatron_id_i,chromosome_s,start_i,end_i,strand_s,donor_s,acceptor_s,samples_t,read_coverage_by_sample_t,samples_count_i,coverage_count_i,coverage_sum_i,coverage_avg_d,coverage_median_d'
SAMPLE_HEADER=""

def run_tabix(args,filter_set=None,sample_set=None,filtering=False):
    #args_=shlex.split("%s %s %s" % (TABIX,TABIX_DB,args))
    sys.stderr.write("running %s %s %s\n" % (TABIX,TABIX_DB,args))
    if not filtering:
        sys.stdout.write("Type\t%s\n" % (INTRON_HEADER))
    ids_found=set()
    #tabixp = subprocess.Popen(args_,stdout=subprocess.PIPE,shell=True)
    tabixp = subprocess.Popen("%s %s %s" % (TABIX,TABIX_DB,args),stdout=subprocess.PIPE,shell=True)
    for line in tabixp.stdout:
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
        #now just stream back the result
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

def main():
    input_ = sys.argv[1]
    (tabix_input,solr_input) = input_.split('|')
    samples = load_sample_metadata(SAMPLE_MD_FILE) 
    sys.stderr.write("loaded %d samples metadata\n" % (len(samples)))
    sample_set=set()
    filter_set=None
    if len(solr_input) >= 1:
       #filter_set=set() 
       filter_set = stream_solr(solr_input,filter_set=None,sample_set=None)
       sys.stderr.write("found %d introns in solr\n" % (len(filter_set)))
    #run_tabix(tabix_input,filter_set=filter_set,sample_set=sample_set)
    if len(tabix_input) >= 1:
       run_tabix(tabix_input,filter_set=filter_set,sample_set=sample_set)
       sys.stderr.write("found %d samples\n" % (len(sample_set)))
    #if filter_set != None:
    #    stream_solr(solr_input,filter_set=filter_set,sample_set=sample_set) 
    #stream_samples(sample_set,samples)

if __name__ == '__main__':
    main()
