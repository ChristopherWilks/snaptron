#!/usr/bin/env python2.7
'''
Takes sample and sample ID queries.
Returns list of sample metadata and/or intron IDs mapping to the sample queries.
'''

import sys
import os
import subprocess
import json
import time

import gzip

import lucene
from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.search import TermQuery
from org.apache.lucene.search import NumericRangeQuery
from org.apache.lucene.index import IndexReader
from org.apache.lucene.index import Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.queryparser.classic import MultiFieldQueryParser
from org.apache.lucene.search import BooleanClause
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

import snapconf
import snaputil
import snaptron

DEBUG_MODE=False

#setup lucene reader for sample related searches
lucene.initVM()
analyzer = StandardAnalyzer(Version.LUCENE_4_10_1)
reader = IndexReader.open(SimpleFSDirectory(File("lucene/")))
searcher = IndexSearcher(reader)

def lucene_sample_query_parse(sampleq):
    #queries_ = sampleq.split(snapconf.SAMPLE_QUERY_DELIMITER)
    fields = []
    queries = []
    booleans = []
    for query_tuple in sampleq:
        (field,query) = query_tuple.split(snapconf.SAMPLE_QUERY_FIELD_DELIMITER)
        field_w_type = snapconf.SAMPLE_HEADER_FIELDS_TYPE_MAP[field]
        fields.append(field_w_type)
        query = query.replace('AND',' AND ')
        sys.stderr.write("query + fields: %s %s\n" % (query,field_w_type))
        queries.append(query)
        booleans.append(BooleanClause.Occur.MUST)
    return (fields,queries,booleans)

#based on the example code at
#http://graus.nu/blog/pylucene-4-0-in-60-seconds-tutorial/
def search_samples_lucene(sample_map,sampleq,sample_set,stream_sample_metadata=False):
    (fields,queries,booleans) = lucene_sample_query_parse(sampleq)
    query = MultiFieldQueryParser.parse(Version.LUCENE_4_10_1, queries, fields, booleans, analyzer)
    #query = MultiFieldQueryParser.parse(Version.LUCENE_4_10_1, ['human AND adult AND brain'], ['description_t'], [BooleanClause.Occur.MUST], analyzer)
    hits = searcher.search(query, snapconf.LUCENE_MAX_SAMPLE_HITS)
    if DEBUG_MODE: 
        sys.stderr.write("Found %d document(s) that matched query '%s':\n" % (hits.totalHits, sampleq))
    if stream_sample_metadata:
        sys.stdout.write("DataSource:Type\t%s\n" % (snapconf.SAMPLE_HEADER))
    for hit in hits.scoreDocs:
        doc = searcher.doc(hit.doc)
        sid = doc.get("intropolis_sample_id_i")
        #track the sample ids if asked to
        if sample_set != None:
            sample_set.add(sid)
        #stream back the full sample metadata record from the in-memory dictionary
        if stream_sample_metadata:
            sys.stdout.write("%s:S\t%s\n" % (snapconf.DATA_SOURCE,sample_map[sid]))

def stream_samples(sample_set,sample_map):
    sys.stdout.write("DataSource:Type\t%s\n" % (snapconf.SAMPLE_HEADER))
    for sample_id in sample_set:
        sys.stdout.write("%s:S\t%s\n" % (snapconf.DATA_SOURCE,sample_map[sample_id]))

#use to load samples metadata to be returned
#ONLY when the user requests by overlap coords OR
#coords and/or non-sample metadata thresholds (e.g. coverage)
#otherwise we'll return the whole thing from SOLR instead
def load_sample_metadata(file_):
    start = time.time()
    fmd=snaputil.load_cpickle_file("%s.pkl" % (file_))
    if fmd:
        end = time.time()
        taken = end-start
        #sys.stderr.write("time taken to load samples from pickle: %d\n" % taken)
        return fmd
    start = time.time()
    fmd={}
    #dont need the hash-on-column headers just yet
    with open(file_,"r") as f:
       for line in f:
           line = line.rstrip()
           fields=line.split("\t")
           fmd[fields[0]]=line
    end = time.time()
    taken = end-start
    #sys.stderr.write("time taken to load samples from normal: %d\n" % taken)
    snaputil.store_cpickle_file("%s.pkl" % (file_),fmd)
    return fmd

#this does the reverse: given a set of sample ids,
#return all the introns associated with each sample
#UPDATE: BROKEN needs to be re-written using TABIX sample2intron ids
def intron_ids_from_samples(sample_set,snaptron_ids):
    start = time.time()
    sample2introns=snaputil.load_cpickle_file("./sample2introns.pkl")
    #print("setting up sample2intron map")
    if not sample2introns:
        sample2introns={}
        #f=open("/data2/gigatron2/all_SRA_introns_ids_stats.tsv.new","r")
        f=gzip.open("%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.TABIX_INTERVAL_DB),"r")
        print("opened gzip file for introns")
        num_lines = 0
        for line in f:
            if "gigatron_id" in line or "snaptron_id" in line:
                continue
            fields=line.rstrip().split('\t')
            sample_ids=fields[snapconf.SAMPLE_IDS_COL].split(',')
            #print("loading line %s" % line) 
            #just map the intron id
            for sample_id in sample_ids:
                if sample_id not in sample2introns:
                    sample2introns[sample_id]=set()
                sample2introns[sample_id].add(int(fields[snapconf.INTRON_ID_COL+1]))
            num_lines+=1
            if num_lines % 10000 == 0:
                print("loaded %d introns" % (num_lines))
        f.close()
    #print("about to write pkl file")
    snaputil.store_cpickle_file("./sample2introns.pkl",sample2introns)
    #print("pkl file written")
    end = time.time()
    taken=end-start
    if DEBUG_MODE:
        sys.stderr.write("loaded %d samples2introns in %d\n" % (len(sample2introns),taken))
    introns_seen=set()
    for sample_id in sample_set:
        introns_seen.update(sample2introns[sample_id])
    if DEBUG_MODE:
        sys.stderr.write("s2I\t%s\n" % (str(len(introns_seen))))
    snaptron_ids.update(introns_seen)
    #return introns_seen

def query_samples(sampleq,sample_map,snaptron_ids,stream_sample_metadata=False):
    sample_ids = set()
    search_samples_lucene(sample_map,sampleq,sample_ids,stream_sample_metadata=stream_sample_metadata)
    new_snaptron_ids = set() 
    if DEBUG_MODE:
        sys.stderr.write("found %d samples matching sample metadata fields/query\n" % (len(sample_ids)))
    if not stream_sample_metadata:
        snaptron_ids_from_samples = set()
        intron_ids_from_samples(sample_ids,snaptron_ids_from_samples)
        new_snaptron_ids = snaptron_ids_from_samples
        if len(snaptron_ids) > 0 and len(snaptron_ids_from_samples) > 0:
            new_snaptron_ids = snaptron_ids.intersection(snaptron_ids_from_samples)
    return new_snaptron_ids


def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    (intervalq,idq,rangeq,sampleq) = snaptron.process_params(input_)
    #only care about sampleq
    if len(intervalq) > 0 or len(rangeq['rfilter']) > 0 or snapconf.SNAPTRON_ID_PATT.search(input_):
        sys.stderr.write("bad input asking for intervals and/or ranges, only take sample queries and/or sample ids, exiting\n")
        sys.exit(-1) 
    sample_map = load_sample_metadata(snapconf.SAMPLE_MD_FILE)
    if DEBUG_MODE:
        sys.stderr.write("loaded %d samples metadata\n" % (len(sample_map)))
    snaptron_ids = set()
    #we're just streaming back sample metadata
    query_samples(sampleq,sample_map,snaptron_ids,stream_sample_metadata=True)
     

if __name__ == '__main__':
    main()
