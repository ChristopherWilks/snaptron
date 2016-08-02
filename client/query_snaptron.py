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


fmap = {'thresholds':'rfilter','filters':'sfilter','region':'regions'}
breakpoint_patt = re.compile(r'^[^:]+-[^:]+$')
def parse_query_argument(args, record, fieldnames, groups):
    endpoint = 'snaptron'
    query=[]
    for field in fieldnames:
        if len(record[field]) > 0:
            if field == 'thresholds' or field == 'filters':
                predicates = re.sub("=",":",record[field])
                predicates = predicates.split('&')
                query.append("&".join(["%s=%s" % (fmap[field],x) for x in predicates]))
            elif field == 'group':
                groups.append(record[field])
            else:
                mapped_field = field
                if field in fmap:
                    mapped_field = fmap[field]
                query.append("%s=%s" % (mapped_field,record[field]))
            if field == 'region' and breakpoint_patt.search(record[field]) is not None:
                endpoint = 'breakpoint'
    if args.function is not None:
        query.append("header=0")
    return (query,endpoint)


def parse_command_line_args(args):
    fieldnames = []
    endpoint = 'snaptron'
    #for field in (['region', 'thresholds', 'filters', 'contains', 'exact', 'within']):
    for field in clsnapconf.FIELD_ARGS.keys():
        if field in vars(args) and vars(args)[field] is not None:
            fieldnames.append(field)
    groups = []
    (query,endpoint) = parse_query_argument(args, vars(args), fieldnames, groups)
    return (["&".join(query)], groups, endpoint)


def parse_query_params(args):
    if args.query_file is None:
        return parse_command_line_args(args)
    endpoint = 'snaptron'
    queries = []
    groups = []
    with open(args.query_file,"r") as cfin:
        creader = csv.DictReader(cfin,dialect=csv.excel_tab)
        for (i,record) in enumerate(creader):
            (query, endpoint) = parse_query_argument(args, record, creader.fieldnames, groups)
            queries.append("&".join(query))
    #assume the endpoint will be the same for all lines in the file
    return (queries,groups,endpoint)


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
        sample_scores[sample]=numer/float(denom)
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
    (query_params_per_region,groups,endpoint)=parse_query_params(args)
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
                if len(groups) > 0 and len(groups[group_idx]) > 0:
                    group_label = "%s\t" % (groups[group_idx])
                sys.stdout.write("%s%s\n" % (group_label,record))
    if args.function:
        scores = summary_function(sample_stats,group_list,sample_records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Snaptron command line client')
    for (field,settings) in clsnapconf.FIELD_ARGS.iteritems():
        parser.add_argument("--%s" % field, metavar=settings[0], type=settings[1], default=settings[2], help=settings[3])

    #parser.add_argument('queries', metavar='"query"', type=str, nargs='+', help='raw query directly passed to the web services as is')
    
    parser.add_argument('--query-file', metavar='/path/to/file_with_queries', type=str, default=None, help='path to a file with one query per line where a query is one or more of a region (HUGO genename or genomic interval) optionally with one or more thresholds and/or filters specified and/or contained flag turned on')

    parser.add_argument('--function', metavar='jir', type=str, default=None, help='function to compute between specified groups of junctions ranked across samples; currently only supports Junction Inclusion Ratio (JIR)')

    #parser.add_argument('--fusions', metavar='gene1-gene2', type=str, default=None, help='a list of one or more gene pairs present in a fusion database (currently only COSMIC) which have simple breakpoints definitions for which to run the JIR on; simple is defined here as those which have a single coordinate range for each gene')

    parser.add_argument('--tmpdir', metavar='/path/to/tmpdir', type=str, default=clsnapconf.TMPDIR, help='path to temporary storage for downloading and manipulating junction and sample records')

    #returned format (UCSC, and/or subselection of fields) option?
    #intersection or union of intervals option?

    args = parser.parse_args()
    if args.region is None and args.thresholds is None and args.filters is None and args.query_file is None:
        sys.stderr.write("no discernible arguments passed in, exiting\n")
        parser.print_help()
        sys.exit(-1)
    main(args)
