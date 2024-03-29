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


import sys
import os
import subprocess
import re
import shlex
import urllib
import urllib2
import time
import json
import logging
import gzip
import sqlite3

import lucene
from java.io import File
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.index import IndexReader

#do this to avoid full paths to python scripts in tracebacks, for security
if sys.path[0] != './':
    sys.path=['./'] + sys.path

import snapconf
import snapconfshared as sc
import snaputil
import snample
import snannotation
import snquery


FORCE_SQLITE=False
FORCE_TABIX=False

#return formats:
TSV=sc.TSV
UCSC_BED=sc.UCSC_BED
UCSC_URL=sc.UCSC_URL

EITHER_START=sc.EITHER_START
EITHER_END=sc.EITHER_END

RegionArgs = sc.RegionArgs
default_region_args = sc.default_region_args
logger = default_region_args.logger

sconn = None
snc = None

def search_introns_by_ids(ids,rquery,filtering=False,region_args=default_region_args):
    #TODO also process rquery as part of the SQL
    ra = region_args
    select = 'SELECT * from intron WHERE snaptron_id in'
    found_snaptron_ids = set()
    if len(ids) == 0:
        return (set(),set())
    results = snaputil.retrieve_from_db_by_ids(snc,select,ids)
    #now get methods for 1) header output and 2) intron output (depending on request)
    (header_method,streamer_method) = snaputil.return_formats[ra.return_format]
    header_method(sys.stdout,region_args=ra,interval=ra.coordinate_string)
    #exit early as we only want the ucsc_url
    if ra.return_format == UCSC_URL:
        return (set(),set())
    for intron in results:
        found_snaptron_ids.update(set([str(intron[0])])) 
        if ra.stream_back:
            streamer_method(sys.stdout,None,intron,ra)
    return (found_snaptron_ids,set())


def range_query_parser(rangeq,snaptron_ids):
    '''this method is only used if we need to *filter* by one or more ranges during an interval or sample search'''
    rquery=None
    if rangeq is None or len(rangeq) < 1:
        return None
    filters = rangeq.get('rfilter',[])
    for filter_ in filters:
        m=sc.RANGE_QUERY_FIELD_PATTERN.search(filter_)
        (col,op_,val)=re.split(sc.RANGE_QUERY_OPS,filter_)
        if not m or not col or col not in sc.TABIX_DBS or col not in sc.LUCENE_TYPES:
            continue
        op=m.group(1)
        if op not in sc.operators:
            snaputil.log_error(str(op), "range query operator, exiting")
            sys.exit(-1)
        #queries by id are a different type of query, we simply record the id
        #and then move on, if there is only an id query that will be caught higher up
        if col == 'snaptron_id':
            snaptron_ids.update(set(val.split('-')))
            continue
        (ltype,ptype,qtype) = sc.LUCENE_TYPES[col]
        if op != ':' and ptype == str:
            snaputil.log_error(str(op), "operator, which must be '=' for type string comparison in range query, exiting")
            sys.exit(-1)
        if not rquery:
            rquery = {}
        val=ptype(val)
        rquery[col]=(sc.operators[op],val)
    return rquery

def determine_index_to_use(interval,rangeq,ra):
    if FORCE_TABIX or (not FORCE_SQLITE and (rangeq is None or len(rangeq) < 1 or len(rangeq['rfilter']) < 1)):
        return snquery.RunExternalQueryEngine(sc.TABIX,interval,rangeq,set(),region_args=ra)
    return snquery.RunExternalQueryEngine(sc.SQLITE,interval,rangeq,set(),region_args=ra)
        
def search_by_gene_name(gc,geneq,rangeq,rquery,intron_filters=None,save_introns=False,print_header=True,region_args=default_region_args):
    iids = set()
    sids = set()
    for (chrom,coord_tuples) in gc.gene2coords(geneq):
        for coord_tuple in coord_tuples:
            (st,en) = coord_tuple
            ra = region_args._replace(range_filters=rquery,intron_filter=intron_filters,print_header=print_header,save_introns=save_introns)
            runner = determine_index_to_use("%s:%d-%d" % (chrom,st,en), rangeq, ra)
            (iids_,sids_) = runner.run_query()
            print_header = False
            if save_introns:
                iids.update(iids_)
                sids.update(sids_)
    return (iids,sids)

                  
def process_post_params(input_,region_args=default_region_args):
    '''takes the more extensible JSON from a POST and converts it into a basic query assuming only 1 value per distinct argument'''
    jstring = list(input_)
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
        (intervals,ranges,samples,ids,ra) = parse_json_query(clause,region_args=ra)
        or_intervals.append(intervals)
        or_ranges.append(ranges)
        or_samples.append(samples)
        or_ids.append(ids)
    return (or_intervals,or_ranges,or_samples,or_ids,ra)

def parse_json_query(clause,region_args=default_region_args):
    logger.debug("clause %s\n"  % (clause))
    ra = region_args
    #legacy_remap = {'gene':'genes','interval':'intervals','metadata_keyword':'metadata_keywords'}
    legacy_remap = {}
    fields={}
    fmap={'rfilter':[]}
    for field in sc.JSON_FIELDS:
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
            if field not in sc.RANGE_FIELDS:
                #adjust to map intervals and genes to same array
                if field == 'genes':
                    field = 'intervals'
                if field not in fmap:
                    fmap[field]=[]
                #allow more than one snaptron id, but convert to a ',' separated list
                if field == 'ids':
                    fmap[field].extend(clause[submitted_fname])
                elif field == 'sample_fields':
                    fmap[field].append(clause[submitted_fname])
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
    if 'sample_fields' in fmap:
        fields = fmap['sample_fields']
        ra=ra._replace(sample_fields=fields[0].split(','))
    rangeqs = {'rfilter':fmap['rfilter']}
    return (intervalqs,rangeqs,sampleqs,idqs,ra)


def query_ids(idq,snaptron_ids):
    snaptron_ids.update(set(idq))


def query_regions(intervalq,rangeq,snaptron_ids,filtering=False,region_args=default_region_args):
    rquery = range_query_parser(rangeq,snaptron_ids)
    #intervals/genes are OR'd, but all ranges are ANDed together with each interval/gene search
    print_header = region_args.print_header
    snaptron_ids_returned = set()
    sample_ids_returned = set()
    gc = None
    #make sure we run any R * + M queries through Tabix
    global FORCE_TABIX
    if region_args.sid_search_object is not None:
        FORCE_TABIX = True
    for interval in intervalq:
        ids = None
        sids = None
        if sc.INTERVAL_PATTERN.search(interval):
            ra = region_args._replace(range_filters=rquery,intron_filter=snaptron_ids,print_header=print_header,save_introns=filtering)
            #if we have JUST an interval do tabix (faster) otherwise run against slqite
            runner = determine_index_to_use(interval,rangeq,ra)
            (ids,sids) = runner.run_query()
        else:
            if gc is None:
                gc = snannotation.GeneCoords()
            #if we're searching for a specific gene_id (e.g. ENSG*.2) then we need to require an exact coordinate match
            if snapconf.GENE_ID_PATTERN.search(interval):
                region_args = region_args._replace(exact=True)
            (ids,sids) = search_by_gene_name(gc,interval,rangeq,rquery,intron_filters=snaptron_ids,save_introns=filtering,print_header=print_header,region_args=region_args)
        print_header = False
        if filtering:
            snaptron_ids_returned.update(ids)
            sample_ids_returned.update(sids)
    return (snaptron_ids_returned,sample_ids_returned)

def process_params(input_,region_args=default_region_args):
    params = {'regions':[],'ids':[],'sids':[],'rfilter':[],'sfilter':[],'fields':[],'result_count':False,'contains':'0','either':'0','exact':'0','return_format':TSV,'score_by':'samples_count','coordinate_string':'','header':'1','id':1,'label':'','calc':0,'calc_axis':1,'calc_op':'sum'}
    prefix = region_args.prefix
    header = region_args.header

    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        #only expect one group per query
        if key == 'group':
            prefix = val
            #this can be overriden by an actual label value if one is passed in
            params['label'] = val
            region_args = region_args._replace(label=val)
            header = header.replace(sc.DATA_SOURCE_HEADER, 'Group') 
        elif key not in params:
            snaputil.log_error(key, "query parameter, exiting")
            sys.exit(-1)
        elif key == 'regions' or key == 'ids' or key == 'sids':
            subparams = val.split(',')
            if key == 'sids' and not subparams[0].isdigit():
                #load compilation specific group_id2sample_ids map
                sample_group_map = snaputil.load_sample_group_map()
                try:
                    [params[key].extend(sample_group_map[sgroup].split(',')) for sgroup in subparams]
                except KeyError as e:
                    raise Exception("one or more sample groupings not found: %s\n" % (urllib.quote(str(e))))
            else:
                params[key].extend(subparams)
        elif key == 'id':
            params['ids'].append(val)
        elif key == 'fields':
            if val == 'rc':
                #only provide the total count of results
                params['result_count'] = True
                continue
            subparams = val.split(',')
            if not subparams[0].isdigit() and subparams[0] not in region_args.fields_map:
                #load compilation specific group_id2sample_ids map
                sample_group_map = snaputil.load_sample_group_map()
                try:
                    snaputil.REQ_FIELDS = [region_args.fields_map[field] for sgroup in subparams for field in sample_group_map[sgroup].split(',')]
                except KeyError as e:
                    raise Exception("one or more sample groupings not found: %s\n" % (urllib.quote(str(e))))
            else:
                #note likely due to buffering, a smaller record size will delay first output by ~15 seconds
                snaputil.REQ_FIELDS = [region_args.fields_map[field] for field in subparams]
        elif key == 'rfilter':
            #url decode the rfilters:
            val = urllib.unquote(val)
            params[key].append(val) 
        else:
            if isinstance(params[key], list):
                params[key].append(val) 
            else:
                params[key] = val
                #directly update the main config structure (region_args) with simple parameters
                region_args = region_args._replace(**{key:val})
    #make sure we copy the list of samples over from sids to REQ_FIELDS if this is a bases query
    #bases queries don't support the normal sample IDs filtering mechanism
    if region_args.app == sc.BASES_APP and len(params['sids']) > 0:
        #pick up chromosome,start,end columns first
        snaputil.REQ_FIELDS = [0,1,2]
        snaputil.REQ_FIELDS.extend(region_args.fields_map[field] for field in params['sids'])
        #clear the sample IDs so we don't invoke the normal sample filter processing
        params['sids']=[]
    #turn off header if we're doing calcuations on the return (summarizing)
    if bool(region_args.calc):
        params['header']=0
    #simple_params = set(['result_count','score_by','return_format','coordinate_string','header','calc','calc_axis','calc_op','label'])
    ra=region_args._replace(post=False,contains=bool(int(params['contains'])),either=(int(params['either'])),exact=bool(int(params['exact'])),print_header=bool(int(params['header'])),original_input_string=input_,sids=params['sids'],prefix=prefix,header=header)
    #basic checks against injection attacks for provided params that will be passed to the command line
    if ra.calc_axis not in sc.calc_axis_ops or ra.calc_op not in sc.calc_axis_ops or (len(ra.label) > 0 and sc.label_pattern.search(ra.label) == None):
        raise Exception("bad input for one or more calc/label parameters: %s\n" % (urllib.quote(" ".join([str(x) for x in [ra.calc, ra.calc_axis, ra.calc_op, ra.label]]))))
    return (params['regions'],params['ids'],{'rfilter':params['rfilter']},params['sfilter'],ra)


def run_toplevel_AND_query(intervalq,rangeq,sampleq,idq,sample_map=[],ra=default_region_args):
    #first we build filter-by-snaptron_id list based either (or all) on passed ids directly
    #and/or what's dervied from the sample query and/or what sample ids were passed in as well
    #NOTE this is the only place where we have OR logic, i.e. the set of snaptron_ids passed in
    #and the set of snaptron_ids dervied from the passed in sample_ids are OR'd together in the filtering

    snaptron_ids = set()
    if len(idq) >= 1:
        query_ids(idq,snaptron_ids)

    #if we have any sample related queries, do them to get filter set for later jx querying
    if len(sampleq) > 0 or len(ra.sids) > 0:
        sid_search_automaton = snample.query_samples_fast(sampleq,sample_map,snaptron_ids,ra)
        ra = ra._replace(sid_search_object=sid_search_automaton)

    #end result here is that we have a list of snaptron_ids to filter by
    #or if no snaptron_ids were found we're done, in keeping with the strict AND policy (currently)
    #TODO: update this when we start supporting OR in the POSTs, this will need to change
    if len(snaptron_ids) == 0 and ra.sid_search_object is None and (len(idq) >=1 or len(sampleq) >= 1 or len(ra.sids) >= 1):
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
        ra_ = ra._replace(tabix_db_file=sc.TABIX_DBS['snaptron_id'],stream_back=True)
        (found_snaptron_ids,found_sample_ids) = search_introns_by_ids(snaptron_ids,rquery,filtering=ra_.result_count,region_args=ra_)
    #finally if there's no interval OR id query to use with tabix, use a point range query (first_rquery) with additional filters from the following point range queries and/or ids in lucene
    #UPDATE: disable this since we can't do a recalculation based on a projection of the samples
    elif len(rangeq) >= 1:
        sys.stdout.write("Filter and filter + metadata queries not supported at this time\n")
        #runner = RunExternalQueryEngine(sc.SQLITE,None,rangeq,snaptron_ids,region_args=ra)
        #(found_snaptron_ids,found_sample_ids) = runner.run_query()
    
    if ra.result_count:
        sys.stdout.write("%d\n" % (len(found_snaptron_ids)))

record_types_map={'junction':(sc.TABIX_INTERVAL_DB,sc.SNAPTRON_SQLITE_DB,sc.INTRON_HEADER,'I'),sc.GENES_APP:(sc.GENE_TABIX_DB,sc.GENE_SQLITE_DB,sc.GENE_HEADER,'G'),sc.EXONS_APP:(sc.EXON_TABIX_DB,sc.EXON_SQLITE_DB,sc.EXON_HEADER,'E'),sc.BASES_APP:(sc.BASE_TABIX_DB,None,snapconf.BASE_HEADER,'B')}
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
    inputs = input_.split('|')
    (tabix_db,sqlite_db,header,prefix) = record_types_map['junction']
    if inputs[0] in record_types_map:
        (tabix_db,sqlite_db,header,prefix) = record_types_map[inputs[0]]
        input_ = '|'.join(inputs[1:])
    global sconn
    if sqlite_db is not None:
        sconn = sqlite3.connect(sqlite_db)
        global snc
        snc = sconn.cursor()
    global FORCE_SQLITE
    global FORCE_TABIX
    if len(sys.argv) == 3:
       loggger.setLevel(logging.DEBUG)
    if len(sys.argv) == 4:
       FORCE_SQLITE=True
    if len(sys.argv) == 5:
       FORCE_TABIX=True
    if input_ == "PIPE":
        input_ = sys.stdin.read()
    (intervalq,rangeq,idq) = (None,None,None)
    sampleq = []
    sample_map = snample.load_sample_metadata(sc.SAMPLE_MD_FILE)
    #make copy of the region_args tuple
    ra = default_region_args
    #override defaults for the DB files in case we're doing gene/exon rather than junction queries
    ra=ra._replace(tabix_db_file=tabix_db,sqlite_db_file=sqlite_db,header="%s\t%s" % (sc.DATA_SOURCE_HEADER,header), prefix="%s:%s" % (snapconf.DATA_SOURCE,prefix))
    #if doing a base-level query, switch the snaptron_id,start,end fields to be appropriate, we re-use the start col for the ID field to be an integer
    if inputs[0] == sc.BASES_APP:
        ra=ra._replace(id_col=sc.BASE_START_COL,region_start_col=sc.BASE_START_COL,region_end_col=sc.BASE_END_COL,fields_map=snapconf.BASE_HEADER_FIELDS_MAP,fields_list=snapconf.BASE_HEADER_FIELDS,app=sc.BASES_APP)
    #bulk query mode
    #somewhat ad hoc, but with the first test
    #trying to avoid a pattern search across the whole input string
    #which could be large
    change_header_print_status=False
    if input_[:6] == 'group=' or 'group=' in input_:
        for query in re.split(sc.BULK_QUERY_DELIMITER,input_):
            (intervalq,idq,rangeq,sampleq,ra) = process_params(query,region_args=ra)
            if change_header_print_status:
                ra=ra._replace(print_header=False)
            run_toplevel_AND_query(intervalq,rangeq,sampleq,idq,sample_map=sample_map,ra=ra)
            change_header_print_status = True
    elif '[' in input_:
        (or_intervals,or_ranges,or_samples,or_ids,ra) = process_post_params(input_)
        for idx in (xrange(0,len(or_intervals))):
            run_toplevel_AND_query(or_intervals[idx],or_ranges[idx],or_samples[idx],or_ids[idx],sample_map=sample_map,ra=ra)
            ra=ra._replace(print_header=False)
    #update support simple '&' CGI format
    else:
        (intervalq,idq,rangeq,sampleq,ra) = process_params(input_,region_args=ra)
        run_toplevel_AND_query(intervalq,rangeq,sampleq,idq,sample_map=sample_map,ra=ra)


if __name__ == '__main__':
    main()
