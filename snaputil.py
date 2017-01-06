#!/usr/bin/env python2.7
import os
import re
import cPickle
import gzip
import urllib

import numpy as np

import snapconf
import snapconfshared

RegionArgs = snapconfshared.RegionArgs
default_region_args = snapconfshared.default_region_args

#return formats:
TSV=snapconfshared.TSV
UCSC_BED=snapconfshared.UCSC_BED
UCSC_URL=snapconfshared.UCSC_URL

REQ_FIELDS=[]

def load_cpickle_file(filepath, compressed=False):
    ds = None
    if os.path.exists(filepath):
        if compressed:
            with gzip.GzipFile(filepath,"rb") as f:
                ds=cPickle.load(f)
        else: 
            with open(filepath,"rb") as f:
                ds=cPickle.load(f)
    return ds

def store_cpickle_file(filepath, ds, compress=False):
    if not os.path.exists(filepath):
        if compress:
            with gzip.GzipFile(filepath,"wb") as f:
                cPickle.dump(ds,f,cPickle.HIGHEST_PROTOCOL)
        else:
            with open(filepath,"wb") as f:
                cPickle.dump(ds,f,cPickle.HIGHEST_PROTOCOL)
        return True
    return False

def retrieve_from_db_by_ids(dbh,select,ids):
    #bug from snaptronUI
    ids.discard("snaptron_id")
    wheres = ['?' for x in ids]
    select = "%s (%s);" % (select,','.join(wheres))
    ids_ = [int(id_) for id_ in ids]
    return dbh.execute(select,ids_)

def sqlite3_interval_query_parse(qargs,where,arguments,ra):
    if qargs is None:
        return (None,None,None)
    m = snapconf.TABIX_PATTERN.search(qargs)
    chrom = m.group(1)
    start = m.group(2)
    end = m.group(3)
    where_="chrom=? AND end>=? AND start<=?"
    if ra.contains:
        where_="chrom=? AND start>=? AND end<=?"
    where.append(where_)
    start = int(start)
    end = int(end)
    arguments.append(chrom) 
    arguments.append(start) 
    arguments.append(end) 
    return (chrom,start,end)

def sqlite3_range_query_parse(rquery,where,arguments):
    for query_string in rquery['rfilter']:
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
            if col == 'annotated':
                val = str(val)
                #special casing for the annotated field since it's a mix of integer and string
                if (len(val) > 1 or val == '1'):
                    val = '0'
                    op='!='
            where.append("%s %s ?" % (col,op))
            #only need ptype ("python type") for this version of parser
            (ltype,ptype,qtype) = snapconf.LUCENE_TYPES[col]
            #do some input cleansing to avoid injection attacks
            val = val.replace("'","")
            val = val.replace('"','')
            arguments.append(ptype(val))
    return where

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
        newline = "\t".join([str(fields[x]) for x in REQ_FIELDS]) + "\n"
    elif line is None:
        newline = "\t".join(map(str, fields)) + '\n'
    if not ra.prefix:
        fout.write("%s" % (newline))
    else:
        fout.write("%s\t%s" % (ra.prefix,newline))

return_formats={TSV:(stream_header,stream_intron),UCSC_BED:(ucsc_format_header,ucsc_format_intron),UCSC_URL:(ucsc_url,None)}

#def extract_sids_and_covs_from_search_iter(samples_found_iter, samples_str, num_samples):
def extract_sids_and_covs_from_search_iter(samples_found_iter, fields):
    samples_str = fields[snapconf.SAMPLE_IDS_COL]
    found = np.empty((0,2),dtype=np.int32)
    idx = 0
    samples = ""
    #for (pos,sid) in samples_found_iter:
    try:
        while(True):
            (pos, sid) = samples_found_iter.next()
            i = pos+1
            cov = ""
            while(i < len(samples_str) and samples_str[i] != ','):
                cov+=samples_str[i]
                i+=1
            found = np.append(found, [[int(sid),int(cov)]], 0)
            samples+=","+sid+":"+cov
            idx+=1
    except StopIteration:
        if idx == 0:
            return (None,None)
    length = len(found)
    #newfields = [samples,length,np.sum(found[0:length,1]),np.mean(found[0:length,1]),np.median(found[0:length,1])]
    fields[snapconf.SAMPLE_IDS_COL] = samples
    fields[snapconf.SAMPLE_IDS_COL+1] = length
    fields[snapconf.SAMPLE_IDS_COL+2] = np.sum(found[0:length,1])
    fields[snapconf.SAMPLE_IDS_COL+3] = np.mean(found[0:length,1])
    fields[snapconf.SAMPLE_IDS_COL+4] = np.median(found[0:length,1])
    return (found,fields)



def filter_by_ranges(fields,rquerys):
    skip=False
    for rfield in rquerys.keys():
        (op,rval)=rquerys[rfield]
        if rfield not in snapconf.INTRON_HEADER_FIELDS_MAP:
            sys.stderr.write("bad field %s in range query,exiting\n" % (rfield))
            sys.exit(-1)
        fidx = snapconf.INTRON_HEADER_FIELDS_MAP[rfield]
        (ltype,ptype,qtype) = snapconf.LUCENE_TYPES[rfield]
        if rfield == 'annotated':
            val = str(fields[fidx])
            rval = str(rval)
            #special casing for the annotated field since it's a mix of integer and string
            if ((len(val) > 1 or val == '1') and rval == '0') or (val == '0' and rval == '1'):
                skip=True
                break
        else:
            val=ptype(fields[fidx])
            if not op(val,rval):
                skip=True
                break
    return skip
