#!/usr/bin/env python2.7

# This file is part of Snaptron.
#
# Snaptron is free software: you can redistribute it and/or modify
# it under the terms of the 
#
#    The MIT License
#
#    Copyright (c) 2016-  by Christopher Wilks <broadsword@gmail.com> 
#                         and Ben Langmead <langmea@cs.jhu.edu>
#
#    Permission is hereby granted, free of charge, to any person obtaining
#    a copy of this software and associated documentation files (the
#    "Software"), to deal in the Software without restriction, including
#    without limitation the rights to use, copy, modify, merge, publish,
#    distribute, sublicense, and/or sell copies of the Software, and to
#    permit persons to whom the Software is furnished to do so, subject to
#    the following conditions:
#
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#    BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#    ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#    SOFTWARE.

'''
Takes sample and sample ID queries.
Returns list of sample metadata and/or intron IDs mapping to the sample queries.
'''

import sys
import os
import subprocess
import json
import time
import re
import urllib
import logging

import gzip


import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.search import BooleanQuery
#from org.apache.lucene.search.BooleanQuery import Builder
from org.apache.lucene.search import LegacyNumericRangeQuery
from org.apache.lucene.index import Term
from org.apache.lucene.search import TermQuery
from org.apache.lucene.search import PhraseQuery
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.index import IndexReader
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import MultiFieldQueryParser
from org.apache.lucene.search import BooleanClause
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

#do this to avoid full paths to python scripts in tracebacks, for security
if sys.path[0] != './':
    sys.path=['./'] + sys.path


import snapconf
import snapconfshared as sc
import snaputil
import snaptron
import snquery
import logging
import lucene_indexer

default_region_args = sc.default_region_args
logger = default_region_args.logger

BOOLEAN_OCCUR=BooleanClause.Occur.MUST

searchers = []
std_reader = DirectoryReader.open(SimpleFSDirectory(Paths.get(sc.LUCENE_STD_SAMPLE_DB)))
std_searcher = IndexSearcher(std_reader)
searchers.append(std_searcher)

ws_reader = DirectoryReader.open(SimpleFSDirectory(Paths.get(sc.LUCENE_WS_SAMPLE_DB)))
ws_searcher = IndexSearcher(ws_reader)
searchers.append(ws_searcher)

def read_lucene_field_types_file(file_in):
    ftypes = {}
    with open(file_in, "r") as fin:
        for line in fin:
            (fieldname, fieldtypechar) = line.rstrip().split('\t')
            lucene_type_method = TermQuery
            if fieldtypechar in lucene_indexer.LUCENE_TYPE_METHODS:
                lucene_type_method = lucene_indexer.LUCENE_TYPE_METHODS[fieldtypechar]
            ftypes[fieldname]=[fieldtypechar, lucene_type_method]
    return ftypes

def lucene_range_query_parse(field_w_type, op, val, fieldtypechar, ftype_method):
    '''parse the user's range query string into something pylucene can understand'''
    ptype = int
    if fieldtypechar == 'f':
        ptype = float
    (start, end) = (ptype(val), ptype(val)) 
    start_inclusive = True
    end_inclusive = True
    #assume operator == '='
    if op == '>:':
        end = None 
    if op == '<:':
        start = None 
    if op == '<':
        start = None
        end_inclusive = False
    if op == '>':
        end = None
        start_inclusive = False
    return ftype_method(field_w_type, lucene_indexer.PREC_STEP, start, end, start_inclusive, end_inclusive)


def lucene_sample_query_parse(sampleq, ftypes):
    fields = []
    queries = []
    booleans = []
    bq = BooleanQuery.Builder()
    for query_tuple in sampleq:
        (field, op_, value) = re.split(sc.RANGE_QUERY_OPS, query_tuple)
        m=sc.RANGE_QUERY_FIELD_PATTERN.search(query_tuple)
        if m is None or field is None:
            continue
        op=m.group(1)
        if op not in sc.operators:
            snaputil.log_error(str(op), "range query operator, exiting")
            sys.exit(-1)
        field_w_type = snapconf.SAMPLE_HEADER_FIELDS_TYPE_MAP[field]
        (fieldtypechar, ftype_method) = ftypes[field_w_type]
        #range query
        if fieldtypechar == 'i' or fieldtypechar == 'f':
            bq.add(lucene_range_query_parse(field_w_type, op, value, fieldtypechar, ftype_method), BOOLEAN_OCCUR)
        #phrase query
        elif ' ' in value or '\t' in value:
            pquery = PhraseQuery.Builder()
            [pquery.add(Term(field_w_type, v.lower())) for v in re.split(r'\s+',value)]
            #force exact phrase matching only
            pquery.setSlop(0)
            bq.add(pquery.build(), BOOLEAN_OCCUR)
        #term query
        else:
            bq.add(TermQuery(Term(field_w_type, value.lower())), BOOLEAN_OCCUR)
        logger.debug("value + fields: %s %s\n" % (urllib.quote(value.lower()), field_w_type))
    return bq.build()


#based on the example code at
#http://graus.nu/blog/pylucene-4-0-in-60-seconds-tutorial/
def search_samples_lucene(sample_map,sampleq,sample_set,ra,stream_sample_metadata=False):
    #still useful for local tracking of sample IDs
    #even if we don't need them higher up in the stack
    if sample_set is None:
        sample_set = set()
    ftypes = read_lucene_field_types_file(lucene_indexer.LUCENE_TYPES_FILE)
    query = lucene_sample_query_parse(sampleq, ftypes)
    #do a non-redundant union of the 2 analyzers and 2 lucene DB types
    header = ra.print_header
    for searcher in searchers:
        hits = searcher.search(query, sc.LUCENE_MAX_SAMPLE_HITS)
        logger.debug("%s %s Found %d document(s) that matched query '%s':\n" % (searcher, query, hits.totalHits, sampleq))
        if stream_sample_metadata and header:
            sys.stdout.write("DataSource:Type\tLucene TF-IDF Score\t%s\n" % (snapconf.SAMPLE_HEADER))
            header = False
        for hit in hits.scoreDocs:
            doc = searcher.doc(hit.doc)
            sid = str(doc.get(snapconf.SAMPLE_ID_FIELD_NAME))
            #track the sample ids if asked to
            if sid != None and len(sid) >= 1 and sid not in sample_set and sid in sample_map:
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
    logger.debug("time taken to load samples from normal: %d\n" % taken)
    snaputil.store_cpickle_file("%s.pkl" % (file_),fmd)
    return fmd

def sample_ids2intron_ids_from_db(sample_ids):
    select = 'SELECT snaptron_ids FROM by_sample_id WHERE sample_id in'
    found_snaptron_ids = set()
    results = snaputil.retrieve_from_db_by_ids(sc,select,sample_ids)
    for snaptron_ids in results:
        found_snaptron_ids.update(set(snaptron_ids[0].split(',')))
    if '' in found_snaptron_ids:
        found_snaptron_ids.remove('')
    return found_snaptron_ids

def sample_ids2intron_ids_from_bit_vector(sample_ids):
    snaptron_ids_final = None
    for sample_id in sample_ids:
        snaptron_ids = snaputil.load_cpickle_file("%s/%s.pkl" % (sc.PACKED_SAMPLE_IDS_PATH, str(sample_id)), compressed=False)
        #in a few cases we may not have a mapping for a specific sample_id
        if snaptron_ids is None:
            continue
        if snaptron_ids_final is None:
            snaptron_ids_final = snaptron_ids
        else:
            snaptron_ids_final = snaptron_ids_final | snaptron_ids
    snaptron_ids_final_set = set()
    [snaptron_ids_final_set.add(str(i)) for (i,x) in enumerate(snaptron_ids_final) if x]
    return snaptron_ids_final_set

#this does the reverse: given a set of sample ids,
#return all the introns associated with each sample
def intron_ids_from_samples(sample_ids,snaptron_ids,rquery,filtering=False):
    if sample_ids is None or len(sample_ids) == 0:
        return
    start = time.time()
    sample_ids2intron_ids = sample_ids2intron_ids_from_db
    #GTEx has a much denser set of snaptron_ids (junctions) per sample_id than SRAv2
    #bit vectors work better with the denser mapping
    if snapconf.DATA_SOURCE == 'GTEx':
        sample_ids2intron_ids = sample_ids2intron_ids_from_bit_vector
    found_snaptron_ids = sample_ids2intron_ids(sample_ids)
    end = time.time()
    taken=end-start
    snaptron_ids.update(found_snaptron_ids)


def query_samples_fast(sampleq,sample_map,snaptron_ids,ra,stream_sample_metadata=False):
    sample_ids = set()
    #maybe the user wants to pass in sample IDs directly
    if len(ra.sids) > 0:
        sample_ids = set(ra.sids)
        logger.debug("user submitted %d sample IDs\n" % (len(sample_ids)))
    #otherwise search via metadata
    else:
        search_samples_lucene(sample_map,sampleq,sample_ids,ra,stream_sample_metadata=stream_sample_metadata)
        logger.debug("found %d samples matching sample metadata fields/query\n" % (len(sample_ids)))
    sid_search_automaton = None
    if not stream_sample_metadata and len(sample_ids) > 0:
        sid_search_automaton = snquery.build_sid_ahoc_queries(sample_ids)
    return sid_search_automaton

def query_samples(sampleq,sample_map,snaptron_ids,ra,stream_sample_metadata=False):
    sample_ids = set()
    search_samples_lucene(sample_map,sampleq,sample_ids,ra,stream_sample_metadata=stream_sample_metadata)
    new_snaptron_ids = set()
    logger.debug("found %d samples matching sample metadata fields/query\n" % (len(sample_ids)))
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
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
        #debugging turned on
       logger.setLevel(logging.DEBUG)
    if input_ == "PIPE":
        input_ = sys.stdin.read()
    (intervalq,rangeq,sampleq,idq) = (None,None,None,None)
    ra = snaptron.default_region_args
    if input_[0] == '[' or input_[1] == '[' or input_[2] == '[':
        (or_intervals,or_ranges,or_samples,or_ids,ra) = snaptron.process_post_params(input_)
        (intervalq,rangeq,sampleq,idq) = (or_intervals[0],or_ranges[0],or_samples[0],or_ids[0])
    else:
        #first, some special cases
        #1) just stream back the whole sample metadata file
        if 'all=1' in input_:
            #sample_map = load_sample_metadata(sc.SAMPLE_MD_FILE)
            cmd = 'cat'
            if '.gz' in sc.SAMPLE_MD_FILE:
                cmd = 'zcat'
            subp = subprocess.Popen('%s %s' % (cmd,sc.SAMPLE_MD_FILE),shell=True,stdin=None,stdout=sys.stdout,stderr=sys.stderr)
            subp.wait()
            return
        #2) check the date of the source sample metadata file (for client caching purposes)
        elif 'check_for_update=1' in input_:
            stats = os.stat(sc.SAMPLE_MD_FILE)
            sys.stdout.write(str(stats.st_mtime) + "\n")
            return
        #update support simple '&' CGI format
        (intervalq,idq,rangeq,sampleq,ra) = snaptron.process_params(input_)
    #only care about sampleq
    if len(intervalq) > 0 or len(rangeq['rfilter']) > 0 or sc.SNAPTRON_ID_PATT.search(input_):
        snaputil.log_error(None, "bad input asking for intervals and/or ranges, only take sample queries and/or sample ids, exiting")
        sys.exit(-1) 
    sample_map = load_sample_metadata(sc.SAMPLE_MD_FILE)
    logger.debug("loaded %d samples metadata\n" % (len(sample_map)))
    #main decision cases
    if len(idq) > 0:
        query_by_sample_ids(idq,sample_map,ra)
    elif len(sampleq) > 0:
        snaptron_ids = set()
        #we're just streaming back sample metadata
        query_samples(sampleq,sample_map,snaptron_ids,ra,stream_sample_metadata=True)
     

if __name__ == '__main__':
    main()
