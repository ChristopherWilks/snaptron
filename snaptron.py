#!/usr/bin/env python2.7

import sys
import os
import subprocess
import re
import shlex
from collections import namedtuple
import urllib2
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

DEBUG_MODE=True

#setup lucene reader for sample related searches
lucene.initVM()
analyzer = StandardAnalyzer(Version.LUCENE_4_10_1)
reader = IndexReader.open(SimpleFSDirectory(File("lucene/")))
searcher = IndexSearcher(reader)

#setup lucene reader for range related searches
rreader = IndexReader.open(SimpleFSDirectory(File("/data2/gigatron2/lucene_ranges/")))
rsearcher = IndexSearcher(rreader)

def filter_by_ranges(fields,rquerys):
    skip=False
    for rfield in rquerys.keys():
        (op,rval)=rquerys[rfield]
        if rfield not in snapconf.INTRON_HEADER_FIELDS_MAP:
            sys.stderr.write("bad field %s in range query,exiting\n" % (rfield))
            sys.exit(-1)
        fidx = snapconf.INTRON_HEADER_FIELDS_MAP[rfield]
        (ltype,ptype,qtype) = snapconf.LUCENE_TYPES[rfield]
        val=ptype(fields[fidx])
        #val = float(fields[fidx])
        #if rfield not in snapconf.FLOAT_FIELDS:
        #    val = int(val)
        if not op(val,rval):
            skip=True
            break
    return skip


def run_tabix(qargs,rquerys,tabix_db,intron_filters=None,sample_filters=None,save_introns=False,save_samples=False,stream_back=True,print_header=True,debug=True):
    tabix_db = "%s/%s" % (snapconf.TABIX_DB_PATH,tabix_db)
    filter_by_introns = (intron_filters != None and len(intron_filters) > 0)
    filter_by_samples = (sample_filters != None and len(sample_filters) > 0)
    if debug:
        sys.stderr.write("running %s %s %s\n" % (snapconf.TABIX,tabix_db,qargs))
    if not stream_back and print_header:
        sys.stdout.write("DataSource:Type\t%s\n" % (snapconf.INTRON_HEADER))
    ids_found=set()
    samples_set=set()
    tabixp = subprocess.Popen("%s %s %s | cut -f 2-" % (snapconf.TABIX,tabix_db,qargs),stdout=subprocess.PIPE,shell=True)
    for line in tabixp.stdout:
        fields=line.rstrip().split("\t")
        #now filter, this order is important (filter first, than save ids/print)
        if filter_by_introns and fields[snapconf.INTRON_ID_COL] not in intron_filters:
            #sys.stderr.write("field %s not in filter_set\n" % (fields[snapconf.INTRON_ID_COL]))
            continue
        if rquerys and filter_by_ranges(fields,rquerys):
            continue
        #combine these two so we only have to split sample <= 1 times
        if filter_by_samples or save_samples:
            samples = set(fields[snapconf.SAMPLE_IDS_COL].split(","))
            if filter_by_samples:
                have_samples = sample_filters.intersection(samples)
                if len(have_samples) == 0:
                    #sys.stderr.write("field %s not in filter_set\n" % (fields[snapconf.INTRON_ID_COL]))
                    continue
            if save_samples:
                sample_set.update(samples)
        #filter return stream based on range queries (if any)
        if stream_back:
            sys.stdout.write("%s:I\t%s" % (snapconf.DATA_SOURCE,line))
        if save_introns:
            ids_found.add(fields[snapconf.INTRON_ID_COL])
    exitc=tabixp.wait() 
    if exitc != 0:
        raise RuntimeError("%s %s %s returned non-0 exit code\n" % (snapconf.TABIX,tabix_db,qargs))
    return (ids_found,samples_set)


def lucene_sample_query_parse(sampleq):
    queries_ = sampleq.split(snapconf.SAMPLE_QUERY_DELIMITER)
    fields = []
    queries = []
    booleans = []
    for query_tuple in queries_:
        #(field,query) = query_tuple.split(snapconf.SAMPLE_QUERY_FIELD_DELIMITER)
        fields.append(field)
        query = query.replace('AND',' AND ')
        #sys.stderr.write("query + fields: %s %s\n" % (query,field))
        queries.append(query)
        booleans.append(BooleanClause.Occur.MUST)
    return (fields,queries,booleans)


def lucene_range_query_parse(query_string):
    '''parse the user's range query string into something pylucene can understand'''
    query = BooleanQuery()
    queries_ = query_string.split(snapconf.RANGE_QUERY_DELIMITER)
    start = None
    end = None
    start_inclusive = True
    end_inclusive = True
    for query_tuple in queries_:
        m=snapconf.RANGE_QUERY_FIELD_PATTERN.search(query_tuple)
        (col,op_,val)=re.split(snapconf.RANGE_QUERY_OPS,query_tuple)
        if not m or not col or col not in snapconf.TABIX_DBS or col not in snapconf.LUCENE_TYPES:
            continue
        op=m.group(1)
        if op not in snapconf.operators:
            sys.stderr.write("bad operator %s in range query,exiting\n" % (str(op)))
            sys.exit(-1)
        (ltype,ptype,qtype) = snapconf.LUCENE_TYPES[col]
        rquery = None
        if ptype == str:
            rquery = TermQuery(qtype(col,str(val)))
        else:
            #assume operator == '='
            (start,end) = (ptype(val),ptype(val)) 
            if op == '>=':
                end = None 
            if op == '<=':
                start = None 
            if op == '<':
                start = None
                end_inclusive = False
            if op == '>':
                end = None
                start_inclusive = False
            rquery = qtype(col,start,end,start_inclusive,end_inclusive)
        query.add(rquery,BooleanClause.Occur.MUST)
        #sys.stderr.write("query + fields: %s %s\n" % (query,field))
    return query

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


#based on the example code at
#http://graus.nu/blog/pylucene-4-0-in-60-seconds-tutorial/
def search_ranges_lucene(rangeq,snaptron_ids,stream_back=False):
    parsed_query = lucene_range_query_parse(rangeq)
    hits = rsearcher.search(parsed_query, snapconf.LUCENE_MAX_RANGE_HITS)
    if DEBUG_MODE: 
        sys.stderr.write("Found %d document(s) that matched range query '%s':\n" % (hits.totalHits, parsed_query))
    if stream_back:
        sys.stdout.write("DataSource:Type\t%s\n" % (snapconf.INTRON_HEADER))
    for hit in hits.scoreDocs:
        doc = rsearcher.doc(hit.doc)
        sid = doc.get("snaptron_id")
        #stream back the full record from the record in Lucene
        if stream_back and (snaptron_ids == None or len(snaptron_ids) == 0 or sid in snaptron_ids):
            sys.stdout.write("%s:I\t%s\n" % (snapconf.DATA_SOURCE,doc.get('all')))
        #track the sample ids if asked to
        elif snaptron_ids != None:
            snaptron_ids.add(sid)
           
 
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

#do multiple searches by a set of ids
def search_introns_by_ids(snaptron_ids,rquery,filtering=False):
    sid_queries = []
    start_sid = 1    
    end_sid = 1
    #coalesce the snaptron_ids into ranges
    #to avoid making too many queries (n+1) to Tabix
    for sid in sorted(snaptron_ids):
        sid = int(sid)
        dist = abs(sid - start_sid)
        if dist <= snapconf.MAX_DISTANCE_BETWEEN_IDS:
           end_sid = sid
        else:
           sid_queries.append("1:%d-%d" % (start_sid,end_sid))
           start_sid = sid
           end_sid = sid
    sid_queries.append("1:%d-%d" % (start_sid,end_sid))
    print_header = True
    found_snaptron_ids = set()
    for query in sid_queries:
        if DEBUG_MODE:
            sys.stderr.write("query %s\n" % (query))
        (ids,sample_ids) = run_tabix(query,rquery,snapconf.TABIX_DBS['snaptron_id'],intron_filters=snaptron_ids,save_introns=filtering,print_header=print_header,debug=DEBUG_MODE)
        if filtering:
            found_snaptron_ids.update(ids)
        print_header = False
    return found_snaptron_ids

#this does the reverse: given a set of sample ids,
#return all the introns associated with each sample
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
    
def range_query_parser(rangeq,snaptron_ids):
    '''this method is only used if we need to *filter* by one or more ranges during an interval or sample search'''
    rquery=None
    if rangeq is None or len(rangeq) < 1:
        return None
    fields = rangeq.split(',')
    for field in fields:
        m=snapconf.RANGE_QUERY_FIELD_PATTERN.search(field)
        (col,op_,val)=re.split(snapconf.RANGE_QUERY_OPS,field)
        if not m or not col or col not in snapconf.TABIX_DBS or col not in snapconf.LUCENE_TYPES:
            continue
        op=m.group(1)
        if op not in snapconf.operators:
            sys.stderr.write("bad operator %s in range query,exiting\n" % (str(op)))
            sys.exit(-1)
        #queries by id are a different type of query, we simply record the id
        #and then move on, if there is only a id query that will be caught higher up
        if col == 'snaptron_id':
            snaptron_ids.update(set(val.split('-')))
            continue
        (ltype,ptype,qtype) = snapconf.LUCENE_TYPES[col]
        if op != '=' and ptype == str:
            sys.stderr.write("operator must be '=' for type string comparison in range query (it was %s), exiting\n" % (str(op)))
            sys.exit(-1)
        if not rquery:
            rquery = {}
        val=ptype(val)
        rquery[col]=(snapconf.operators[op],val)
    return rquery

def parse_id_query(idq,snaptron_ids,sample_ids):
    fields = idq.split(';')
    if len(fields) > 2:
        sys.stderr.write("upto 2 ID fields allowed (snaptron_id and/or sample_id) in the ID query section, exiting\n")
        sys.exit(-1)
    for field in fields:
        (id_type,ids) = field.split(':')
        if id_type == 'snaptron_id':
            snaptron_ids.update(set(ids.split(',')))
        else:
            sample_ids.update(set(ids.split(',')))


def search_by_gene_name(geneq,rquery,intron_filters=None,save_introns=False):
    gene_map = {}
    with open("%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.REFSEQ_ANNOTATION),"r") as f:
        for line in f:
            fields = line.rstrip().split('\t')
            (gene_name,chrom,st,en) = (fields[0].upper(),fields[2],int(fields[4]),int(fields[5]))
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
    geneq = geneq.upper()
    if geneq not in gene_map:
        sys.stderr.write("ERROR no gene found by name %s\n" % (geneq))
        sys.exit(-1)
    print_header = True
    iids = set()
    sids = set()
    for (chrom,coord_tuples) in sorted(gene_map[geneq].iteritems()):
        for coord_tuple in coord_tuples:
            (st,en) = coord_tuple
            (iids_,sids_) = run_tabix("%s:%d-%d" % (chrom,st,en),rquery,snapconf.TABIX_INTERVAL_DB,intron_filters=intron_filters,print_header=print_header,save_introns=save_introns)
            print_header = False
            if save_introns:
                iids.update(iids_)
                sids.update(sids_)
    return (iids,sids)


#cases:
#1) just interval (one function call)
#2) interval + range query(s) (one tabix function call + field filter(s))
#3) one or more range queries (one tabix range function call + field filter(s))
#4) interval + sample (2 function calls: 1 lucene for sample filter + 1 tabix using snaptron_id filter)
#5old) sample (1 lucene call -> use interval ids to return all intervals)
#5) sample (1 lucene call -> use snaptron_ids to do a by_ids search (multiple tabix calls))
#6) sample + range query(s) (2 function calls: 1 lucene for sample filter + 1 tabix using snaptron_id filter + field filter)
def main():
    input_ = sys.argv[1]
    DEBUG_MODE_=DEBUG_MODE
    if len(sys.argv) > 2:
        DEBUG_MODE_=True
    (intervalq,rangeq,sampleq,idq) = input_.split('|')
    sample_map = load_sample_metadata(snapconf.SAMPLE_MD_FILE)
    if DEBUG_MODE_:
        sys.stderr.write("loaded %d samples metadata\n" % (len(sample_map)))

    #first we build filter-by-snaptron_id list based either (or all) on passed ids directly
    #and/or what's dervied from the sample query and/or what sample ids were passed in as well
    #NOTE this is the only place where we have OR logic, i.e. the set of snaptron_ids passed in
    #and the set of snaptron_ids dervied from the passed in sample_ids are OR'd together in the filtering
    snaptron_ids = set()
    if len(idq) >= 1:
        sample_ids = set()
        parse_id_query(idq,snaptron_ids,sample_ids)
        if len(sample_ids) > 0:
            intron_ids_from_samples(sample_ids,snaptron_ids)
        #didn't get any snaptron ids here, assuming AND, we quit
        if len(snaptron_ids) == 0:
            return

    #if we have any sample related queries, do them to get snaptron_id filter set
    if len(sampleq) >= 1:
        sample_ids = set()
        search_samples_lucene(sample_map,sampleq,sample_ids,stream_sample_metadata=False)
        if DEBUG_MODE_:
            sys.stderr.write("found %d samples matching sample metadata fields/query\n" % (len(sample_ids)))
        snaptron_ids_from_samples = set()
        intron_ids_from_samples(sample_ids,snaptron_ids_from_samples)
        if len(snaptron_ids) > 0 and len(snaptron_ids_from_samples) > 0:
            snaptron_ids = snaptron_ids.intersection(snaptron_ids_from_samples)
        elif len(snaptron_ids_from_samples) > 0:
            snaptron_ids = snaptron_ids_from_samples
        #if no snaptron_ids were found we're done, in keeping with the strict AND policy (currently)
        if len(snaptron_ids) == 0:
            return

    #end result here is that we have a list of snaptron_ids to filter by

    #NOW start normal query processing between: 1) interval 2) range or 3) or just snaptron ids
    #note: 1) and 3) use tabix, 2) uses lucene
    #sample_set = set()
    #UPDATE: prefer tabix queries of either interval or snaptron_ids rather than lucene search of range queries due to speed
    #if len(snaptron_ids) > 0 and len(intervalq) == 0 and (len(rangeq) == 0 or not first_tdb):
    #back to usual processing, interval queries come first possibly with filters from the point range queries and/or ids
    if len(intervalq) >= 1:
        rquery = range_query_parser(rangeq,snaptron_ids)
        if snapconf.INTERVAL_PATTERN.search(intervalq):
            run_tabix(intervalq,rquery,snapconf.TABIX_INTERVAL_DB,intron_filters=snaptron_ids,debug=DEBUG_MODE_)
        else:
            search_by_gene_name(intervalq,rquery,intron_filters=snaptron_ids)
    elif len(snaptron_ids) >= 1:
        rquery = range_query_parser(rangeq,snaptron_ids)
        search_introns_by_ids(snaptron_ids,rquery)
    #finally if there's no interval OR id query to use with tabix, use a point range query (first_rquery) with additional filters from the following point range queries and/or ids in lucene
    elif len(rangeq) >= 1:
        #run_tabix(first_rquery,rquery,first_tdb,filter_set=snaptron_ids,sample_set=sample_set,debug=DEBUG_MODE_)
        search_ranges_lucene(rangeq,snaptron_ids,stream_back=True)

if __name__ == '__main__':
    main()


#####deprecated
comp_op_pattern=re.compile(r'([=><!]+)')
def range_query_parser_deprecated(rangeq,snaptron_ids,rquery_will_be_index=False):
    rquery={}
    #snaptron_ids = []
    if rangeq is None or len(rangeq) < 1:
        return (None,None,rquery)
    fields = rangeq.split(',')
    (first_tdb,first_rquery)=(None,None)
    for field in fields:
        m=comp_op_pattern.search(field)
        (col,op_,val)=re.split(comp_op_pattern,field)
        if not m or not col or col not in snapconf.TABIX_DBS:
            continue
        op=m.group(1)
        if op not in snapconf.operators:
            sys.stderr.write("bad operator %s in range query,exiting\n" % (str(op)))
            sys.exit(-1)
        #queries by id are a different type of query, we simply record the id
        #and then move on, if there is only a id query that will be caught higher up
        if col == 'snaptron_id':
            snaptron_ids.update(set(val.split('-')))
            continue
        val=float(val)
        if col not in snapconf.FLOAT_FIELDS:
            val=int(val)
        if first_tdb:
            rquery[col]=(snapconf.operators[op],val)
            continue 
            #return (None,None,None,only_ids)
        #add first rquery to the rquery hash if we're not going to be
        #used as an index 
        #OR the case where it's floating point and we need to work around
        #Tabix's lack of support for that
        if not rquery_will_be_index or 'avg' in col or 'median' in col:
            rquery[col]=(snapconf.operators[op],val)
        #if we are used for the index,
        #then for 2nd pass columns where the value could be 0 (GTEx)
        #we need to add another predicate to avoid the 0
        #since tabix doesn't handle 0's and will return them
        #even for a >=1 query
        #elif col[-1] == '2' and val > 0.0:
        #    rquery[col]=(operators['>'],0.0)
        #only do the following for the first range query
        tdb=snapconf.TABIX_DBS[col]
        first_tdb=tdb
        extension=""
        #since tabix only takes integers, round to nearest integer
        val = int(round(val))
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
