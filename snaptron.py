#!/usr/bin/env python2.7

import sys
import os
import subprocess
import re
import shlex
from collections import namedtuple
import urllib
import urllib2
import time
import json

import gzip

import sqlite3

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
import snample
import snannotation

#return formats:
TSV='0'
UCSC_BED='1'
UCSC_URL='2'

RegionArgs = namedtuple('RegionArgs','tabix_db_file range_filters intron_filter sample_filter save_introns save_samples stream_back print_header header prefix cut_start_col region_start_col region_end_col contains result_count return_format score_by post original_input_string coordinate_string debug')

default_region_args = RegionArgs(tabix_db_file=snapconf.TABIX_INTERVAL_DB, range_filters=[], intron_filter=None, sample_filter=None, save_introns=False, save_samples=False, stream_back=True, print_header=True, header="Datasource:Type\t%s" % snapconf.INTRON_HEADER, prefix="%s:I" % snapconf.DATA_SOURCE, cut_start_col=snapconf.CUT_START_COL, region_start_col=snapconf.INTERVAL_START_COL, region_end_col=snapconf.INTERVAL_END_COL, contains=False, result_count=False, return_format=TSV, score_by="samples_count", post=False, original_input_string='', coordinate_string='', debug=True)

sconn = sqlite3.connect(snapconf.SNAPTRON_SQLITE_DB)
snc = sconn.cursor()

DEBUG_MODE=True

REQ_FIELDS = []

#setup lucene reader for range related searches
lucene.initVM()
analyzer = StandardAnalyzer(Version.LUCENE_4_10_1)
rreader = IndexReader.open(SimpleFSDirectory(File(snapconf.LUCENE_RANGE_DB)))
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
        if not op(val,rval):
            skip=True
            break
    return skip

def ucsc_format_header(fout,region_args=default_region_args,interval=None):
    header = ["browser position %s" % (interval)]
    header.append("track name=\"Snaptron\" visibility=2 description=\"Snaptron Exported Splice Junctions\" color=100,50,0 useScore=1\n")
    fout.write("\n".join(header))

def ucsc_format_intron(fout,line,fields,region_args=default_region_args):
    ra = region_args
    new_line = list(fields[1:4])
    new_line.extend(["junc",fields[snapconf.INTRON_HEADER_FIELDS_MAP[ra.score_by]],fields[snapconf.STRAND_COL]])
    #adjust for UCSC BED start-at-0 coordinates
    new_line[snapconf.INTERVAL_START_COL-1] = str(int(new_line[snapconf.INTERVAL_START_COL-1]) - 1)
    fout.write("%s\n" % ("\t".join([str(x) for x in new_line])))

def ucsc_url(fout,region_args=default_region_args,interval=None):
    #change return_format=2 to =1 to actually return the introns in UCSC BED format
    input_str = re.sub("return_format=2","return_format=1",region_args.original_input_string)
    encoded_input_string = urllib.quote(re.sub(r'regions=[^&]+',"regions=%s" % (interval),input_str))
    ucsc_url = "".join(["http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=%s&hgct_customText=" % (snapconf.HG,interval),snapconf.SERVER_STRING,"/snaptron?",encoded_input_string])
    if region_args.print_header:
        fout.write("DataSource:Type\tcoordinate_string\tURL\n")
    fout.write("%s:U\t%s\t%s\n" % (snapconf.DATA_SOURCE,interval,ucsc_url))

def stream_header(fout,region_args=default_region_args,interval=None):
    ra = region_args
    custom_header = ra.header
    #if the user asks for specific fields they only get those fields, no data source
    if len(REQ_FIELDS) > 0:
        custom_header = "DataSource:Type\t%s" % ("\t".join([snapconf.INTRON_HEADER_FIELDS[x] for x in sorted(REQ_FIELDS)]))
        ra = ra._replace(prefix=None)
    if ra.stream_back and ra.print_header:
        if not ra.result_count:
            fout.write("%s\n" % (custom_header))
    if ra.stream_back and ra.print_header and ra.post:
        fout.write("datatypes:%s\t%s\n" % (str.__name__,snapconf.INTRON_TYPE_HEADER))

def stream_intron(fout,line,fields,region_args=default_region_args):
    ra = region_args
    if len(fields) == 0:
        fields = line.split('\t')
    newline = line
    if len(REQ_FIELDS) > 0:
       newline = "\t".join([fields[x] for x in REQ_FIELDS]) + "\n"
    if not ra.prefix:
        fout.write("%s" % (newline))
    else:
        fout.write("%s\t%s" % (ra.prefix,newline))

return_formats={TSV:(stream_header,stream_intron),UCSC_BED:(ucsc_format_header,ucsc_format_intron),UCSC_URL:(ucsc_url,None)}
def run_tabix(qargs,region_args=default_region_args,additional_cmd=""):
    ra = region_args
    m = snapconf.TABIX_PATTERN.search(qargs)
    start = m.group(2)
    end = m.group(3)
    ids_found=set()
    samples_set=set()
    #this trumps whatever stream_back instructions we were given
    if ra.result_count:
        ra = ra._replace(stream_back=False)
        ra = ra._replace(save_introns=True)
    ra = ra._replace(tabix_db_file = "%s/%s" % (snapconf.TABIX_DB_PATH,ra.tabix_db_file))
    filter_by_introns = (ra.intron_filter != None and len(ra.intron_filter) > 0)
    filter_by_samples = (ra.sample_filter != None and len(ra.sample_filter) > 0)
    if ra.debug:
        sys.stderr.write("running %s %s %s\n" % (snapconf.TABIX,ra.tabix_db_file,qargs))
    (header_method,streamer_method) = return_formats[ra.return_format]
    header_method(sys.stdout,region_args=ra,interval=qargs)
    #exit early as we only want the ucsc_url
    if ra.return_format == UCSC_URL:
        return (set(),set())
    if len(additional_cmd) > 0:
        additional_cmd = " | %s" % (additional_cmd)
    tabixp = subprocess.Popen("%s %s %s | cut -f %d- %s" % (snapconf.TABIX,ra.tabix_db_file,qargs,ra.cut_start_col,additional_cmd),stdout=subprocess.PIPE,shell=True)
    for line in tabixp.stdout:
        fields=line.rstrip().split("\t")
        #first attempt to filter by violation of containment (if in effect)
        if ra.contains and (fields[ra.region_start_col] < start or fields[ra.region_end_col] > end):
            continue
        #now filter, this order is important (filter first, than save ids/print)
        if filter_by_introns and fields[snapconf.INTRON_ID_COL] not in ra.intron_filter:
            continue
        if ra.range_filters and filter_by_ranges(fields,ra.range_filters):
            continue
        #combine these two so we only have to split sample <= 1 times
        if filter_by_samples or ra.save_samples:
            samples = set(fields[snapconf.SAMPLE_IDS_COL].split(","))
            if filter_by_samples:
                have_samples = sample_filter.intersection(samples)
                if len(have_samples) == 0:
                    continue
            if ra.save_samples:
                sample_set.update(samples)
        #filter return stream based on range queries (if any)
        if ra.stream_back:
            streamer_method(sys.stdout,line,fields,region_args=ra)
        if ra.save_introns:
            ids_found.add(fields[snapconf.INTRON_ID_COL])
    exitc=tabixp.wait() 
    if exitc != 0:
        raise RuntimeError("%s %s %s returned non-0 exit code\n" % (snapconf.TABIX,ra.tabix_db_file,qargs))
    return (ids_found,samples_set)

def sqlite3_range_query_parse(rquery,where,arguments):
    query_string = rquery['rfilter'][0]
    queries_ = query_string.split(snapconf.RANGE_QUERY_DELIMITER)
    for query_tuple in queries_:
        m=snapconf.RANGE_QUERY_FIELD_PATTERN.search(query_tuple)
        (col,op_,val)=re.split(snapconf.RANGE_QUERY_OPS,query_tuple)
        if not m or not col or col not in snapconf.LUCENE_TYPES:
            continue
        op=m.group(1)
        op=op.replace(':','=')
        if op not in snapconf.operators_old:
            sys.stderr.write("bad operator %s in range query,exiting\n" % (str(op)))
            sys.exit(-1)
        where.append("%s %s ?" % (col,op))
        #only need ptype ("python type") for this version of parser
        (ltype,ptype,qtype) = snapconf.LUCENE_TYPES[col]
        arguments.append(ptype(val))
    return where

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

#if snaptron_ids is passed in with one or more snaptron ids, than filtering by snaptron id is inferred
#and save_introns is assumed to be False
def search_ranges_sqlite3(rangeq,snaptron_ids,stream_back=True):
    arguments = []
    where = []
    #UPDATE try filtering by set first then use it as a sqljoin
    #if len(snaptron_ids) > 0:
    #    where.add("snaptron_id in (%s)" % (','.join(["?" for x in snaptron_ids])))
    #    arguments = [int(id_) for id_ in snaptron_ids]
    sqlite3_range_query_parse(rangeq,where,arguments)
    select = "SELECT * from intron WHERE %s" % (' AND '.join(where))
    sys.stderr.write("%s\n" % select)
    results = snc.execute(select,arguments)
    sids = set()
    for result in results:
        snaptron_id = result[0]
        if stream_back and (not snaptron_ids or len(snaptron_ids) == 0 or snaptron_id in snaptron_ids):
            stream_intron(sys.stdout,"%s\n" % ("\t".join(str(x) for x in result)),result)
        else:
            sids.add(str(snaptron_id))
    return (sids,set())

#based on the example code at
#http://graus.nu/blog/pylucene-4-0-in-60-seconds-tutorial/
def search_ranges_lucene(rangeq,snaptron_ids,stream_back=False,filtering=False):
    parsed_query = lucene_range_query_parse(rangeq)
    hits = rsearcher.search(parsed_query, snapconf.LUCENE_MAX_RANGE_HITS)
    sids = set()
    if DEBUG_MODE: 
        sys.stderr.write("Found %d document(s) that matched range query '%s':\n" % (hits.totalHits, parsed_query))
    if stream_back:
        sys.stdout.write("DataSource:Type\t%s\n" % (snapconf.INTRON_HEADER))
    for hit in hits.scoreDocs:
        doc = rsearcher.doc(hit.doc)
        sid = doc.get("snaptron_id")
        #stream back the full record from the record in Lucene
        if stream_back and (snaptron_ids == None or len(snaptron_ids) == 0 or sid in snaptron_ids):
            stream_intron(sys.stdout,doc.get('all'),[])
        #track the snaptron ids if asked to
        if snaptron_ids != None:
            snaptron_ids.add(sid)
        if filtering:
            sids.add(sid)
    return (sids,set())
           
def search_introns_by_ids(ids,rquery,tabix_db=snapconf.TABIX_DBS['snaptron_id'],filtering=False,region_args=default_region_args):
    ra = region_args
    tabix_db = ra.tabix_db_file
    select = 'SELECT * from intron WHERE snaptron_id in'
    found_snaptron_ids = set()
    results = snaputil.retrieve_from_db_by_ids(snc,select,ids)
    #now get methods for 1) header output and 2) intron output (depending on request)
    (header_method,streamer_method) = return_formats[ra.return_format]
    header_method(sys.stdout,region_args=ra,interval=ra.coordinate_string)
    #exit early as we only want the ucsc_url
    if ra.return_format == UCSC_URL:
        return (set(),set())
    for intron in results:
        found_snaptron_ids.update(set([str(intron[0])])) 
        if ra.stream_back:
            streamer_method(sys.stdout,"%s\n" % "\t".join([str(x) for x in intron]),intron,ra)
    return (found_snaptron_ids,set())


#do multiple searches by a set of ids
def search_introns_by_ids_old(ids,rquery,tabix_db=snapconf.TABIX_DBS['snaptron_id'],filtering=False):
    '''
    search by EITHER snaptron_id(s) OR sample_id(s)
    '''
    sid_queries = []
    start_sid = 1    
    end_sid = 1
    #coalesce the ids into ranges
    #to avoid making too many queries (n+1 problem) to Tabix
    for sid in sorted(int(x) for x in ids):
        #offset ids by one since the actual tabix search starts at 1
        #but the ids themselves start at 0
        sid = int(sid) + 1
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
        #(retrieved_ids,sample_ids) = run_tabix(query,rquery,tabix_db,intron_filters=ids,save_introns=filtering,print_header=print_header,cut_start_col=snapconf.ID_START_COL,debug=DEBUG_MODE)
        ra = default_region_args._replace(region_filters=rquery,tabix_db_file=tabix_db,intron_filter=ids,save_introns=filtering,print_header=print_header,cut_start=snapconf.ID_START_COL,debug=DEBUG_MODE)
        (retrieved_ids,sample_ids) = run_tabix(query,region_args=ra)
        if filtering:
            found_snaptron_ids.update(retrieved_ids)
        print_header = False
    return (found_snaptron_ids,set())
   
 
def range_query_parser(rangeq,snaptron_ids):
    '''this method is only used if we need to *filter* by one or more ranges during an interval or sample search'''
    rquery=None
    if rangeq is None or len(rangeq) < 1:
        return None
    filters = rangeq.get('rfilter',[])
    for filter_ in filters:
        m=snapconf.RANGE_QUERY_FIELD_PATTERN.search(filter_)
        (col,op_,val)=re.split(snapconf.RANGE_QUERY_OPS,filter_)
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

def search_by_gene_name(gc,geneq,rquery,intron_filters=None,save_introns=False,print_header=True,region_args=default_region_args):
    iids = set()
    sids = set()
    for (chrom,coord_tuples) in gc.gene2coords(geneq):
        for coord_tuple in coord_tuples:
            (st,en) = coord_tuple
            #(iids_,sids_) = run_tabix("%s:%d-%d" % (chrom,st,en),rquery,snapconf.TABIX_INTERVAL_DB,intron_filters=intron_filters,print_header=print_header,save_introns=save_introns)
            ra = region_args._replace(range_filters=rquery,intron_filter=intron_filters,print_header=print_header,save_introns=save_introns)
            (iids_,sids_) = run_tabix("%s:%d-%d" % (chrom,st,en),region_args=ra)
            print_header = False
            if save_introns:
                iids.update(iids_)
                sids.update(sids_)
    return (iids,sids)

                  
def process_post_params(input_,region_args=default_region_args):
    '''takes the more extensible JSON from a POST and converts it into a basic query assuming only 1 value per distinct argument'''
    jstring = list(input_)
    #get rid of extra quotes
    jstring[0]=''
    jstring[-1]=''
    jstring = ''.join(jstring)
    js = json.loads(jstring)
    #for now assume only one OR clause (so no ORing)
    #clause = js[0]
    ra=region_args._replace(post=True,original_input_string=input_)
    or_intervals = []
    or_ranges = []
    or_samples = []
    or_ids = []
    for clause in js:
        (intervals,ranges,samples,ids) = parse_json_query(clause,region_args=ra)
        or_intervals.append(intervals)
        or_ranges.append(ranges)
        or_samples.append(samples)
        or_ids.append(ids)
    return (or_intervals,or_ranges,or_samples,or_ids,ra)

def parse_json_query(clause,region_args=default_region_args):
    ra = region_args
    #legacy_remap = {'gene':'genes','interval':'intervals','metadata_keyword':'metadata_keywords'}
    legacy_remap = {}
    fields={}
    fmap={'rfilter':[]}
    for field in snapconf.JSON_FIELDS:
        legacy_fieldname = field
        if field in legacy_remap:
            legacy_fieldname = legacy_remap[field]
        if field in clause or legacy_fieldname in clause:
            submitted_fname = field
            if legacy_fieldname in clause:
                submitted_fname = legacy_fieldname
            if field not in fields:
                fields[field]=[]
            #adds array of values to a new entry in this field's array
            fields[field].append(clause[submitted_fname])
            #hack to support legacy query format (temporary), we're only assuming one val per array
            if field not in snapconf.RANGE_FIELDS:
                #adjust to map intervals and genes to same array
                if field == 'genes':
                    field = 'intervals'
                if field not in fmap:
                    fmap[field]=[]
                #allow more than one snaptron id, but convert to a ',' separated list
                if field == 'ids':
                    fmap[field].extend(clause[submitted_fname])
                #otherwise only grab the first one (no nested OR)
                else:
                    fmap[field].append(clause.get(submitted_fname)[0])
            else:
                #for now we just return one range filter (no nested OR)
                rmap = clause.get(submitted_fname)[0]
                fmap['rfilter'].append("%s%s%s" % (field,rmap['op'],rmap['val']))
    #for now we just return one interval/gene (no nested OR)
    intervalqs=[]
    if 'intervals' in fmap:
        intervalqs = [fmap['intervals'][0]]
    #for now we just return one keyword (no nested OR)
    sampleqs = []
    if 'metadata_keywords' in fmap:
        sampleqs = fmap['metadata_keywords'][0]
    idqs = []
    if 'ids' in fmap:
        idqs=fmap['ids']
    rangeqs = {'rfilter':fmap['rfilter']}
    return (intervalqs,rangeqs,sampleqs,idqs)


def query_ids(idq,snaptron_ids):
    #(id_type,first_id) = idq[0].split(':')
    #idq[0] = first_id
    #sample_ids = set()
    #if id_type == 'snaptron':
    snaptron_ids.update(set(idq))
    #else:
    #    sample_ids.update(set(idq))
    #if len(sample_ids) > 0:
    #    snample.intron_ids_from_samples(sample_ids,snaptron_ids)


def query_regions(intervalq,rangeq,snaptron_ids,filtering=False,region_args=default_region_args):
    rquery = range_query_parser(rangeq,snaptron_ids)
    #intervals/genes are OR'd, but all ranges are ANDed together with each interval/gene search
    print_header = region_args.print_header
    snaptron_ids_returned = set()
    sample_ids_returned = set()
    gc = snannotation.GeneCoords()
    for interval in intervalq:
        ids = None
        sids = None
        if snapconf.INTERVAL_PATTERN.search(interval):
           #(ids,sids) = run_tabix(interval,rquery,snapconf.TABIX_INTERVAL_DB,intron_filters=snaptron_ids,debug=DEBUG_MODE,print_header=print_header,save_introns=filtering)
           ra = region_args._replace(range_filters=rquery,intron_filter=snaptron_ids,print_header=print_header,save_introns=filtering,debug=DEBUG_MODE)
           (ids,sids) = run_tabix(interval,region_args=ra)
        else:
           (ids,sids) = search_by_gene_name(gc,interval,rquery,intron_filters=snaptron_ids,print_header=print_header,region_args=region_args)
        print_header = False
        if filtering:
            snaptron_ids_returned.update(ids)
            sample_ids_returned.update(sids)
    return (snaptron_ids_returned,sample_ids_returned)


def process_params(input_,region_args=default_region_args):
    params = {'regions':[],'ids':[],'rfilter':[],'sfilter':[],'fields':[],'result_count':False,'contains':'0','return_format':TSV,'score_by':'samples_count','coordinate_string':'','header':'1'}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            sys.stderr.write("unknown parameter %s, exiting\n" % key)
            sys.exit(-1)
        if key == 'regions' or key == 'ids':
            subparams = val.split(',')
            for subparam in subparams:
                params[key].append(subparam)
        elif key == 'fields':
            fields = val.split(',')
            for field in fields:
                if field == 'rc':
                    #only provide the total count of results
                    params['result_count'] = True
                    continue
                REQ_FIELDS.append(snapconf.INTRON_HEADER_FIELDS_MAP[field])
        elif key == 'rfilter':
            #url decode the rfilters:
            val = urllib.unquote(val)
            params[key].append(val) 
        else:
            if isinstance(params[key], list):
                params[key].append(val) 
            else:
                params[key]=val
    ra=region_args._replace(post=False,result_count=params['result_count'],contains=bool(int(params['contains'])),score_by=params['score_by'],print_header=bool(int(params['header'])),return_format=params['return_format'],original_input_string=input_,coordinate_string=params['coordinate_string'])
    return (params['regions'],params['ids'],{'rfilter':params['rfilter']},params['sfilter'],ra)


def run_toplevel_AND_query(intervalq,rangeq,sampleq,idq,sample_map=[],ra=default_region_args):
    #first we build filter-by-snaptron_id list based either (or all) on passed ids directly
    #and/or what's dervied from the sample query and/or what sample ids were passed in as well
    #NOTE this is the only place where we have OR logic, i.e. the set of snaptron_ids passed in
    #and the set of snaptron_ids dervied from the passed in sample_ids are OR'd together in the filtering

    snaptron_ids = set()
    if len(idq) >= 1:
        query_ids(idq,snaptron_ids)

    #if we have any sample related queries, do them to get snaptron_id filter set
    #NOTE we are NOT currently support sample-id querying
    if len(sampleq) >= 1:
        snaptron_ids = snample.query_samples(sampleq,sample_map,snaptron_ids)

    #end result here is that we have a list of snaptron_ids to filter by
    #or if no snaptron_ids were found we're done, in keeping with the strict AND policy (currently)
    #TODO: update this when we start supporting OR in the POSTs, this will need to change
    if len(snaptron_ids) == 0 and (len(idq) >=1 or len(sampleq) >= 1):
        return

    #NOW start normal query processing between: 1) interval 2) range or 3) or just snaptron ids
    #note: 1) and 3) use tabix, 2) uses lucene
    #sample_set = set()
    #UPDATE: prefer tabix queries of either interval or snaptron_ids rather than lucene search of range queries due to speed
    #if len(snaptron_ids) > 0 and len(intervalq) == 0 and (len(rangeq) == 0 or not first_tdb):
    #back to usual processing, interval queries come first possibly with filters from the point range queries and/or ids
    found_snaptron_ids = set()
    found_sample_ids = set()
    #favor intervals over everything else
    if len(intervalq) >= 1:
        (found_snaptron_ids,found_sample_ids) = query_regions(intervalq,rangeq,snaptron_ids,filtering=ra.result_count,region_args=ra)
    elif len(snaptron_ids) >= 1:
        rquery = range_query_parser(rangeq,snaptron_ids)
        ra_ = ra._replace(tabix_db_file=snapconf.TABIX_DBS['snaptron_id'],stream_back=True)
        (found_snaptron_ids,found_sample_ids) = search_introns_by_ids(snaptron_ids,rquery,filtering=ra_.result_count,region_args=ra_)
    #finally if there's no interval OR id query to use with tabix, use a point range query (first_rquery) with additional filters from the following point range queries and/or ids in lucene
    elif len(rangeq) >= 1:
        #run_tabix(first_rquery,rquery,first_tdb,filter_set=snaptron_ids,sample_set=sample_set,debug=DEBUG_MODE_)
        #(found_snaptron_ids,found_sample_ids) = search_ranges_lucene(rangeq,snaptron_ids,stream_back=True,filtering=RESULT_COUNT)
        (found_snaptron_ids,found_sample_ids) = search_ranges_sqlite3(rangeq,snaptron_ids,stream_back=not ra.result_count)
    
    if ra.result_count:
        sys.stdout.write("%d\n" % (len(found_snaptron_ids)))


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
    (intervalq,rangeq,idq) = (None,None,None)
    sampleq = []
    #(intervalq,rangeq,sampleq,idq) = ([],[],[],[])
    sys.stderr.write("%s\n" % input_)
    sample_map = snample.load_sample_metadata(snapconf.SAMPLE_MD_FILE)
    if DEBUG_MODE_:
        sys.stderr.write("loaded %d samples metadata\n" % (len(sample_map)))
    #make copy of the region_args tuple
    ra = default_region_args
    if input_[0] == '[' or input_[1] == '[' or input_[2] == '[':
        (or_intervals,or_ranges,or_samples,or_ids,ra) = process_post_params(input_)
        #(intervalq,rangeq,sampleq,idq) = (or_intervals[0],or_ranges[0],or_samples[0],or_ids[0])
        for idx in (xrange(0,len(or_intervals))):
            run_toplevel_AND_query(or_intervals[idx],or_ranges[idx],or_samples[idx],or_ids[idx],sample_map=sample_map,ra=ra)
            ra=ra._replace(print_header=False)
    #update support simple '&' CGI format
    else:
        (intervalq,idq,rangeq,sampleq,ra) = process_params(input_)
        run_toplevel_AND_query(intervalq,rangeq,sampleq,idq,sample_map=sample_map,ra=ra)


if __name__ == '__main__':
    main()
