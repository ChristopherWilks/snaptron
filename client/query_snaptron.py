#!/usr/bin/env python2.7
import sys
import os
import urllib
import urllib2
import argparse
import gzip
import csv
import re

import snapconf
import clsnapconf
from SnaptronIteratorHTTP import SnaptronIteratorHTTP

#TODO use python tmp
TMPDIR='/tmp'

def parse_query_params(args):
    queries = []
    groups = []
    with open(args.query_file,"r") as cfin:
        creader = csv.DictReader(cfin,['region','contains','thresholds','filters','group'],dialect=csv.excel_tab)
        for (i,record) in enumerate(creader):
            query=[]
            #TODO format/name check here
            #have to have a region
            query.append("regions=%s" % record['region'])
            group = ''
            if len(record['contains']) > 0:
                query.append('contains=1')
            if record['thresholds'] is not None and len(record['thresholds']) > 0:
                thresholds = record['thresholds']
                thresholds = re.sub("=",":",thresholds)
                thresholds = thresholds.split('&')
                query.append("&".join(["rfilter=%s" % x for x in thresholds]))
            if record['filters'] is not None and len(record['filters']) > 0:
                filters = record['filters']
                filters = filters.split('&')
                query.append("&".join(["sfilter=%s" % x for x in filters]))
            if record['group'] is not None and len(record['group']) > 0:
                group = record['group']
            if args.function is not None:
                query.append("header=0")
            groups.append(group)
            queries.append("&".join(query))
    return (queries,groups)


def junction_inclusion_ratio(sample_stats,group_list,sample_records):
    group_a = group_list[0]
    group_b = group_list[1]
    sample_scores = {}
    for sample in sample_stats:
        if group_a not in sample_stats[sample]:
            sample_stats[sample][group_a]=0
        if group_b not in sample_stats[sample]:
            sample_stats[sample][group_b]=0
        numer = sample_stats[sample][group_b] - sample_stats[sample][group_a]
        denom = sample_stats[sample][group_b] + sample_stats[sample][group_a] + 1
        sample_scores[sample]=float(numer/float(denom))
    missing_sample_ids = set()
    for sample in sorted(sample_scores.keys(),key=sample_scores.__getitem__,reverse=True):
        score = sample_scores[sample]
        if sample not in sample_records:
            missing_sample_ids.add(sample)
            continue
        sample_record = sample_records[sample]
        sys.stdout.write("%s\t%d\t%d\t%s\n" % (str(score),sample_stats[sample][group_a],sample_stats[sample][group_b],sample_record))


def count_sample_coverage_per_group(args, sample_stats, record, group):
    fields = record.split('\t')
    samples = fields[snapconf.SAMPLE_IDS_COL].split(',')
    sample_covs = fields[snapconf.SAMPLE_IDS_COL+1].split(',')
    for (i,sample_id) in enumerate(samples):
        if sample_id not in sample_stats:
            sample_stats[sample_id]={}
        if group not in sample_stats[sample_id]:
            sample_stats[sample_id][group]=0
        sample_stats[sample_id][group]+=int(sample_covs[i])

def download_sample_metadata(args):
    sample_records = {}
    gfout = None
    if clsnapconf.CACHE_SAMPLE_METADTA:
        cache_file = os.path.join(args.tmpdir,"snaptron_sample_metadata_cache.tsv.gz")
        if os.path.exists(cache_file):
            with gzip.open(cache_file,"r") as gfin:
                for line in gfin:
                    line = line.rstrip()
                    fields = line.split('\t')
                    sample_records[fields[0]]=line
            return sample_records
        else:
            gfout = gzip.open(cache_file,"w")
    response = urllib2.urlopen("%s/samples?all=1" % (clsnapconf.SERVICE_URL))
    all_records = response.read()
    all_records = all_records.split('\n')
    for line in all_records:
        fields = line.split('\t')
        sample_records[fields[0]]=line
        if gfout is not None:
            gfout.write("%s\n" % (line))
        line = response.readline()
    if gfout is not None:
        gfout.close()
    return sample_records


compute_functions={'jir':(count_sample_coverage_per_group,junction_inclusion_ratio),None:(None,None)}
def main(args):
    (query_params_per_region,groups)=parse_query_params(args)
    endpoint = 'snaptron'
    sample_stats = {}
    (count_function,summary_function) = compute_functions[args.function]
    sample_records={}
    if args.function:
        sample_records = download_sample_metadata(args)
    group_list = set()
    map(lambda x: group_list.add(x),groups)
    group_list = sorted(group_list)
    for (group_idx,query_param_string) in enumerate(query_params_per_region):
        sIT = SnaptronIteratorHTTP(query_param_string,endpoint)
        for record in sIT:
            if args.function:
                count_function(args,sample_stats,record,groups[group_idx])
            else:
                group_label = ''
                if len(groups[group_idx]) > 0:
                    group_label = "%s\t" % (groups[group_idx])
                sys.stdout.write("%s%s\n" % (group_label,record))
    if args.function:
        scores = summary_function(sample_stats,group_list,sample_records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Snaptron command line client')

    parser.add_argument('--query-file', metavar='/path/to/file_with_queries', type=str, required=True, help='path to a file with one query per line where a query is one or more of a region (HUGO genename or genomic interval) optionally with one or more thresholds and/or filters specified and/or contained flag turned on')

#    parser.add_argument('--groups', metavar='a=chr#:#-#,chr#:#-#;b=chr#:#-#;...', type=str, default='', help='comma separated list of junction groups defined by genomic intervals; records are prefixed with the group name on output')
    parser.add_argument('--function', metavar='jir', type=str, default=None, help='function to compute between specified groups of junctions ranked across samples; currently only supports Junction Inclusion Ratio (JIR)')
    parser.add_argument('--tmpdir', metavar='/path/to/tmpdir', type=str, default=TMPDIR, help='path to temporary storage for downloading and manipulating junction and sample records')

    parser.add_argument('--regions', metavar='chr#:#-#|chr#:#-#|CD99|...', type=str, default='BRCA1', help='one or more genomic regions (gene names and/or genomic intervals) seperated by \'|\' (logical OR) or the name of a file with a list of one or more regions (include one or more \'/\'s to denote a file path)')
    parser.add_argument('--thresholds', metavar='samples_count>=#[&|]coverage_avg=#[&|]...', type=str, default='samples_count>=1000&coverage_avg>100', help='one or more cutoffs for filtering returned junctions; separator is either \'&\' (logical AND) or \'|\' (logical OR)')
    parser.add_argument('--filters', metavar='design_description:cortex[&|]library_layout=PAIRED[&|]...', type=str, default=None, help='one or more filter predicates on the metadata of the samples from which the junctions are derived; separator is either \'&\' (logical AND) or \'|\' (logical OR)')
    parser.add_argument('--contained', action='store_const', const=True, default=False,
                        help='only return junctions whose coordinate span are within one or more of the regions specified')
    #returned format (UCSC, and/or subselection of fields) option?
    #intersection or union of intervals option?

    main(parser.parse_args())
