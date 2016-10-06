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
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
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

import sqlite3
sconn = sqlite3.connect(snapconf.SAMPLE_SQLITE_DB)
sc = sconn.cursor()

DEBUG_MODE=False

#setup lucene reader for sample related searches
lucene.initVM()
analyzer = StandardAnalyzer(Version.LUCENE_4_10_1)
analyzer_ws = WhitespaceAnalyzer(Version.LUCENE_4_10_1)
reader = IndexReader.open(SimpleFSDirectory(File(snapconf.LUCENE_SAMPLE_DB)))
searcher = IndexSearcher(reader)

def lucene_sample_query_parse(sampleq):
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
def search_samples_lucene(sample_map,sampleq,sample_set,ra,stream_sample_metadata=False):
    (fields,queries,booleans) = lucene_sample_query_parse(sampleq)
    #query = MultiFieldQueryParser.parse(Version.LUCENE_4_10_1, queries, fields, booleans, analyzer)
    query = MultiFieldQueryParser.parse(Version.LUCENE_4_10_1, queries, fields, booleans, analyzer_ws)
    #query = MultiFieldQueryParser.parse(Version.LUCENE_4_10_1, ['human AND adult AND brain'], ['description_t'], [BooleanClause.Occur.MUST], analyzer)
    hits = searcher.search(query, snapconf.LUCENE_MAX_SAMPLE_HITS)
    if DEBUG_MODE: 
        sys.stderr.write("Found %d document(s) that matched query '%s':\n" % (hits.totalHits, sampleq))
    if stream_sample_metadata:
        sys.stdout.write("DataSource:Type\tLucene TF-IDF Score\t%s\n" % (snapconf.SAMPLE_HEADER))
    for hit in hits.scoreDocs:
        doc = searcher.doc(hit.doc)
        sid = doc.get("intropolis_sample_id_i")
        #track the sample ids if asked to
        if sample_set != None and len(sid) >= 1:
            sample_set.add(sid)
        #stream back the full sample metadata record from the in-memory dictionary
        if stream_sample_metadata:
            sys.stdout.write("%s:S\t%s\t%s\n" % (snapconf.DATA_SOURCE,str(hit.score),sample_map[sid]))

#when not querying against Lucene
def stream_samples(sample_set,sample_map,ra):
    sys.stdout.write("DataSource:Type\t%s\n" % (snapconf.SAMPLE_HEADER))
    num_columns = len(snapconf.SAMPLE_HEADER_FIELDS)
    if len(ra.sample_fields) > 0:
        num_columns = len(ra.sample_fields)
    default_metadata = "\t".join(["NA" for x in xrange(0,num_columns-1)])
    for sample_id in sorted([int(x) for x in sample_set]):
    #for sample_id in sample_set:
        try:
            if len(ra.sample_fields) > 0:
                sample_fields = sample_map[str(sample_id)].split('\t')
                sys.stdout.write("%s:S\t%s\n" % (snapconf.DATA_SOURCE,'\t'.join([sample_fields[int(x)] for x in ra.sample_fields])))
            else:
                sys.stdout.write("%s:S\t%s\n" % (snapconf.DATA_SOURCE,sample_map[str(sample_id)]))
        #if the sample id is missing just fill with generic 'NA's for now
        except KeyError,ke:
            sys.stdout.write("%s:S\t%s\t%s\n" % (snapconf.DATA_SOURCE,str(sample_id),default_metadata))
            

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

def sample_ids2intron_ids(sample_ids):
    select = 'SELECT snaptron_ids FROM by_sample_id WHERE sample_id in'
    found_snaptron_ids = set()
    results = snaputil.retrieve_from_db_by_ids(sc,select,sample_ids)
    ids = [x[0] for x in results]
    #for snaptron_ids in results:
    #    found_snaptron_ids.update(set(snaptron_ids[0].split(',')))
    s1=','.join(ids)
    found_snaptron_ids.update(s1.split(','))
    if '' in found_snaptron_ids:
        found_snaptron_ids.remove('')
    return found_snaptron_ids


#this does the reverse: given a set of sample ids,
#return all the introns associated with each sample
#UPDATE: BROKEN needs to be re-written using TABIX sample2intron ids
#UPDATE2: tabix vesion too slow (and slightly broken), need to try sqlite3
def intron_ids_from_samples(sample_ids,snaptron_ids,rquery,filtering=False):
    start = time.time()
    #(found_snaptron_ids,sample_ids) = snaptron_new.search_introns_by_ids(sample_ids,rquery,tabix_db=snapconf.TABIX_DBS['sample_id'],filtering=filtering)
    found_snaptron_ids = sample_ids2intron_ids(sample_ids)
    end = time.time()
    taken=end-start
    if DEBUG_MODE:
        sys.stderr.write("s2I\t%s in time %s secs\n" % (str(len(found_snaptron_ids)),str(taken)))
    snaptron_ids.update(found_snaptron_ids)



def query_samples(sampleq,sample_map,snaptron_ids,ra,stream_sample_metadata=False):
    sample_ids = set()
    search_samples_lucene(sample_map,sampleq,sample_ids,ra,stream_sample_metadata=stream_sample_metadata)
    new_snaptron_ids = set() 
    if DEBUG_MODE:
        sys.stderr.write("found %d samples matching sample metadata fields/query\n" % (len(sample_ids)))
    if not stream_sample_metadata:
        snaptron_ids_from_samples = set()
        intron_ids_from_samples(sample_ids,snaptron_ids_from_samples,None)
        new_snaptron_ids = snaptron_ids_from_samples
        if len(snaptron_ids) > 0 and len(snaptron_ids_from_samples) > 0:
            new_snaptron_ids = snaptron_ids.intersection(snaptron_ids_from_samples)
    return new_snaptron_ids

def query_by_sample_ids(idq,sample_map,ra):
    if len(idq) == 0:
        return
    stream_samples(set(idq),sample_map,ra) 

def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    (intervalq,rangeq,sampleq,idq) = (None,None,None,None)
    ra = snaptron.default_region_args
    sys.stderr.write("INPUT_ %s\n" % input_)
    if input_[0] == '[' or input_[1] == '[' or input_[2] == '[':
        (or_intervals,or_ranges,or_samples,or_ids,ra) = snaptron.process_post_params(input_)
        (intervalq,rangeq,sampleq,idq) = (or_intervals[0],or_ranges[0],or_samples[0],or_ids[0])
    else:
        #just stream back the whole sample metadata file
        if 'all=1' in input_:
            #sample_map = load_sample_metadata(snapconf.SAMPLE_MD_FILE)
            cmd = 'cat'
            if '.gz' in snapconf.SAMPLE_MD_FILE:
                cmd = 'zcat'
            subp = subprocess.Popen('%s %s' % (cmd,snapconf.SAMPLE_MD_FILE),shell=True,stdin=None,stdout=sys.stdout,stderr=sys.stderr)
            subp.wait()
            return 
        #update support simple '&' CGI format
        (intervalq,idq,rangeq,sampleq,ra) = snaptron.process_params(input_)
    #only care about sampleq
    if len(intervalq) > 0 or len(rangeq['rfilter']) > 0 or snapconf.SNAPTRON_ID_PATT.search(input_):
        sys.stderr.write("bad input asking for intervals and/or ranges, only take sample queries and/or sample ids, exiting\n")
        sys.exit(-1) 
    sample_map = load_sample_metadata(snapconf.SAMPLE_MD_FILE)
    if DEBUG_MODE:
        sys.stderr.write("loaded %d samples metadata\n" % (len(sample_map)))
    #main decision cases
    if len(idq) > 0:
        query_by_sample_ids(idq,sample_map,ra)
    elif len(sampleq) > 0:
        snaptron_ids = set()
        #we're just streaming back sample metadata
        query_samples(sampleq,sample_map,snaptron_ids,ra,stream_sample_metadata=True)
     

if __name__ == '__main__':
    main()
