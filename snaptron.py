#!/usr/bin/env python2.7

import sys
import os
import subprocess
import re
import shlex
from collections import namedtuple
import urllib2
import time
import json

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
import snample

DEBUG_MODE=True
POST=False

REQ_FIELDS = []
RESULT_COUNT = False
RETURN_ONLY_CONTAINED = False


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
        #val = float(fields[fidx])
        #if rfield not in snapconf.FLOAT_FIELDS:
        #    val = int(val)
        if not op(val,rval):
            skip=True
            break
    return skip


def stream_intron(fout,line,fields):
    if len(fields) == 0:
        fields = line.split('\t')
    newline = line
    if len(REQ_FIELDS) > 0:
       newline = "\t".join([fields[x] for x in REQ_FIELDS]) + "\n"
    #fout.write("%s" % (newline))
    fout.write("%s:I\t%s" % (snapconf.DATA_SOURCE,newline))


def run_tabix(qargs,rquerys,tabix_db,intron_filters=None,sample_filters=None,save_introns=False,save_samples=False,stream_back=True,print_header=True,contains=None,start_col=2,debug=True):
    if contains is None:
        contains = RETURN_ONLY_CONTAINED
    m = snapconf.TABIX_PATTERN.search(qargs)
    #if not m:
    #    sys.stderr.write("bad interval,exiting %s\n" % (qargs))
    #    sys.exit(-1)
    start = m.group(2)
    end = m.group(3)
    ids_found=set()
    samples_set=set()
    #this trumps whatever stream_back instructions we were given
    if RESULT_COUNT:
        stream_back = False
        save_introns = True
    tabix_db = "%s/%s" % (snapconf.TABIX_DB_PATH,tabix_db)
    filter_by_introns = (intron_filters != None and len(intron_filters) > 0)
    filter_by_samples = (sample_filters != None and len(sample_filters) > 0)
    custom_header = snapconf.INTRON_HEADER
    if len(REQ_FIELDS) > 0:
        custom_header = "\t".join([snapconf.INTRON_HEADER_FIELDS[x] for x in sorted(REQ_FIELDS)])
    if debug:
        sys.stderr.write("running %s %s %s\n" % (snapconf.TABIX,tabix_db,qargs))
    if stream_back and print_header:
        if not RESULT_COUNT: #and len(REQ_FIELDS) == 0:
            sys.stdout.write("DataSource:Type\t")
        sys.stdout.write("%s\n" % (custom_header))
    if stream_back and print_header and POST:
        sys.stdout.write("datatypes:%s\t%s\n" % (str.__name__,snapconf.INTRON_TYPE_HEADER))
    tabixp = subprocess.Popen("%s %s %s | cut -f %d-" % (snapconf.TABIX,tabix_db,qargs,start_col),stdout=subprocess.PIPE,shell=True)
    for line in tabixp.stdout:
        fields=line.rstrip().split("\t")
        #first attempt to filter by violation of containment (if in effect)
        if contains and (fields[snapconf.INTERVAL_START_COL] < start or fields[snapconf.INTERVAL_END_COL] > end):
            continue
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
            #sys.stdout.write("%s:I\t%s" % (snapconf.DATA_SOURCE,line))
            stream_intron(sys.stdout,line,fields)
        if save_introns:
            ids_found.add(fields[snapconf.INTRON_ID_COL])
    exitc=tabixp.wait() 
    if exitc != 0:
        raise RuntimeError("%s %s %s returned non-0 exit code\n" % (snapconf.TABIX,tabix_db,qargs))
    return (ids_found,samples_set)




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
            #sys.stdout.write("%s:I\t%s\n" % (snapconf.DATA_SOURCE,doc.get('all')))
            stream_intron(sys.stdout,doc.get('all'),[])
        #track the snaptron ids if asked to
        if snaptron_ids != None:
            snaptron_ids.add(sid)
        if filtering:
            sids.add(sid)
    return (sids,set())
           
#do multiple searches by a set of ids
def search_introns_by_ids(ids,rquery,tabix_db=snapconf.TABIX_DBS['snaptron_id'],filtering=False):
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
        (retrieved_ids,sample_ids) = run_tabix(query,rquery,tabix_db,intron_filters=ids,save_introns=filtering,print_header=print_header,start_col=snapconf.ID_START_COL,debug=DEBUG_MODE)
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

def search_by_gene_name(geneq,rquery,intron_filters=None,save_introns=False,print_header=True):
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


def parse_json_query(input_):
    '''takes the more extensible JSON from a POST and converts it into a basic query assuming only 1 value per distinct argument'''
    jstring = list(input_)
    #get rid of extra quotes
    jstring[0]=''
    jstring[-1]=''
    #jstring = "'%s'" % ''.join(jstring)
    jstring = ''.join(jstring)
    js = json.loads(jstring)
    fields={}
    fmap={'rfilter':[]}
    #fmap = {'intervals':intervals,'genes':intervals,'rangesq':[],'mds':[],'snaptron_id':[]}
    #for now assume only one OR clause (so no ORing)
    clause = js[0]
    for field in snapconf.TABIX_DBS.keys():
        if field == 'chromosome':
            field = 'intervals'
        if field == 'snaptron_id':
            field = 'ids'
        if field in clause:
            if field not in fields:
                fields[field]=[]
            #adds array of values to a new entry in this field's array
            fields[field].append(clause[field])
            #hack to support legacy query format (temporary), we're only assuming one val per array
            if field not in snapconf.RANGE_FIELDS:
                #adjust to map intervals and genes to same array
                if field == 'genes':
                    field = 'intervals'
                if field not in fmap:
                    fmap[field]=[]
                #allow more than one snaptron id, but convert to a ',' separated list
                if field == 'ids':
                    fmap[field].extend(clause[field])
                else:
                    fmap[field].append(clause.get(field)[0])
            else:
                rmap = clause.get(field)[0]
                fmap['rfilter'].append("%s%s%s" % (field,rmap['op'],rmap['val']))
            
    #for now we just return one interval/gene
    intervalqs=[]
    if 'intervals' in fmap:
        intervalqs = [fmap['intervals'][0]]
    #rangeq = ','.join(fmap['rangesq'])
    sampleq = []
    if 'metadata_keywords' in fmap:
        sampleq = fmap['metadata_keywords'][0]
    idq = []
    if 'ids' in fmap:
        #idq.append("snaptron:%s" % (",".join(fmap['snaptron_id'])))
        idq=fmap['ids']
        #idq[0]="snaptron:%s" % idq[0]
    #return ([intervalq],[rangeq],mdq,idq)
    return (intervalqs,{'rfilter':fmap['rfilter']},sampleq,idq)





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




def query_regions(intervalq,rangeq,snaptron_ids,filtering=False):
    rquery = range_query_parser(rangeq,snaptron_ids)
    #intervals/genes are OR'd, but all ranges are ANDed together with each interval/gene search
    print_header = True
    snaptron_ids_returned = set()
    sample_ids_returned = set()
    for interval in intervalq:
        ids = None
        sids = None
        if snapconf.INTERVAL_PATTERN.search(interval):
           (ids,sids) = run_tabix(interval,rquery,snapconf.TABIX_INTERVAL_DB,intron_filters=snaptron_ids,debug=DEBUG_MODE,print_header=print_header,save_introns=filtering)
        else:
           (ids,sids) = search_by_gene_name(interval,rquery,intron_filters=snaptron_ids,print_header=print_header)
        print_header = False
        if filtering:
            snaptron_ids_returned.update(ids)
            sample_ids_returned.update(sids)
    return (snaptron_ids_returned,sample_ids_returned)


def process_params(input_):
    global RESULT_COUNT
    global RETURN_ONLY_CONTAINED
    params = {'regions':[],'ids':[],'rfilter':[],'sfilter':[],'fields':[],'contains':0}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            sys.stderr.write("unknown parameter %s, exiting\n" % param)
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
                    RESULT_COUNT=True
                    continue
                REQ_FIELDS.append(snapconf.INTRON_HEADER_FIELDS_MAP[field])
        elif key == 'contains':
            if val == '1':
                RETURN_ONLY_CONTAINED = True
        else:
            params[key].append(val) 
    return (params['regions'],params['ids'],{'rfilter':params['rfilter']},params['sfilter'])


#cases:
#1) just interval (one function call)
#2) interval + range query(s) (one tabix function call + field filter(s))
#3) one or more range queries (one tabix range function call + field filter(s))
#4) interval + sample (2 function calls: 1 lucene for sample filter + 1 tabix using snaptron_id filter)
#5old) sample (1 lucene call -> use interval ids to return all intervals)
#5) sample (1 lucene call -> use snaptron_ids to do a by_ids search (multiple tabix calls))
#6) sample + range query(s) (2 function calls: 1 lucene for sample filter + 1 tabix using snaptron_id filter + field filter)
def main():
    global POST
    input_ = sys.argv[1]
    DEBUG_MODE_=DEBUG_MODE
    if len(sys.argv) > 2:
       DEBUG_MODE_=True
    (intervalq,rangeq,sampleq,idq) = (None,None,None,None)
    #(intervalq,rangeq,sampleq,idq) = ([],[],[],[])
    sys.stderr.write("%s\n" % input_)
    if input_[0] == '[' or input_[1] == '[' or input_[2] == '[':
        (intervalq,rangeq,sampleq,idq) = parse_json_query(input_)
        POST=True
    #update support simple '&' CGI format
    else:
    #    (intervalq,rangeq,sampleq,idq) = input_.split('|')
        (intervalq,idq,rangeq,sampleq) = process_params(input_)

    sample_map = snample.load_sample_metadata(snapconf.SAMPLE_MD_FILE)
    if DEBUG_MODE_:
        sys.stderr.write("loaded %d samples metadata\n" % (len(sample_map)))

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
    if len(intervalq) >= 1:
        (found_snaptron_ids,found_sample_ids) = query_regions(intervalq,rangeq,snaptron_ids,filtering=RESULT_COUNT)
    elif len(snaptron_ids) >= 1:
        rquery = range_query_parser(rangeq,snaptron_ids)
        (found_snaptron_ids,found_sample_ids) = search_introns_by_ids(snaptron_ids,rquery,filtering=RESULT_COUNT)
    #finally if there's no interval OR id query to use with tabix, use a point range query (first_rquery) with additional filters from the following point range queries and/or ids in lucene
    elif len(rangeq) >= 1:
        #run_tabix(first_rquery,rquery,first_tdb,filter_set=snaptron_ids,sample_set=sample_set,debug=DEBUG_MODE_)
        (found_snaptron_ids,found_sample_ids) = search_ranges_lucene(rangeq,snaptron_ids,stream_back=True,filtering=RESULT_COUNT)
    
    if RESULT_COUNT:
        sys.stdout.write("%d\n" % (len(found_snaptron_ids)))

if __name__ == '__main__':
    main()
