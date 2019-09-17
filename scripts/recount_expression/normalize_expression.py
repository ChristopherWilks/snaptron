#!/usr/bin/env python2.7
import sys
import argparse
import gzip
import clsnaputil

#assumes you already have the AUCs
#pulled out using:
#wiggletools print non_unique_base_coverage.bw.auc AUC non_unique_base_coverage.bw

RECOUNT_TARGET = 40 * 1000000
SNAPTRON_FORMAT_CHR_COL = 1
SNAPTRON_FORMAT_COUNT_COL = 11

def load_metadata(args):
    has_base_coverage_column = False
    with open(args.metadata_file,"rb") as fin:
        lines = fin.read()
        lines = lines.split('\n')
        fields = lines[1].split('\t')
        if lines[len(lines)-1] == '':
            lines.pop()
        if args.auc_col == -1:
            args.auc_col = len(fields) - 1 
        aucs = {}
        sids = []
        for x in lines:
            fields = x.split('\t')
            if fields[0] == 'rail_id':
                has_base_coverage_column = fields[-1] == 'has_base_coverage'
                if has_base_coverage_column and args.auc_col == len(fields) - 1:
                    args.auc_col -= 1
                continue
            if not has_base_coverage_column or fields[-1] == 'true':
                #print fields[args.auc_col]
                aucs[fields[args.sample_id_col]]=fields[args.auc_col]
                sids.append(fields[args.sample_id_col])
        return (aucs, sids)

def normalize_counts(args, aucs, sids):
    header = {}
    if args.snaptron_format:
        sys.stdout.write("gene_id")
        [sys.stdout.write("\t"+x) for x in sids]
        sys.stdout.write("\n")
    with gzip.open(args.counts_file,"rb") as fin:
        #maps column position
        for line in fin:
            fields = None
            fields__ = line.rstrip().split('\t')
            if args.snaptron_format:
                gene_id = fields__[SNAPTRON_FORMAT_CHR_COL] + ':' + '-'.join(fields__[SNAPTRON_FORMAT_CHR_COL+1:SNAPTRON_FORMAT_CHR_COL+3])
                if args.id_type == 'gene_id':
                    gene_id = fields__[SNAPTRON_FORMAT_COUNT_COL-1].split(':')[0]
                fields = {sid:0 for sid in sids}
                for sample in fields__[SNAPTRON_FORMAT_COUNT_COL].split(',')[1:]:
                    (sid, count) = sample.split(':')
                    fields[sid] = int(count)
            else:
                gene_id = fields__[0]
                if gene_id == 'gene_id' or gene_id == 'Group':
                    sys.stdout.write(line)
                    sids = fields__[args.count_start_col:]
                    continue
                else:
                    fields = {sids[i]:int(count) for (i,count) in enumerate(fields__[args.count_start_col:])}
            fields = [int(clsnaputil.round_like_R((RECOUNT_TARGET * float(fields[sid]))/float(aucs[sid]),0)) for sid in sids]
            if args.skip_0_rows:
                zeros = [1 for x in fields if x == 0]
                if len(zeros) == len(fields):
                    continue
            sys.stdout.write(gene_id+"\t"+"\t".join(map(str,fields))+"\n")

def main():
    parser = argparse.ArgumentParser(description='Normalization of raw counts')
    parser.add_argument('--counts-file', metavar='/path/to/counts_file', type=str, default=None, help='path to a TSV file with matrix of counts', required=True)
    parser.add_argument('--metadata-file', metavar='/path/to/sample_metadata_file', type=str, default=None, help='path to a TSV file with the Snaptron sample metadata', required=True)
    parser.add_argument('--auc-col', metavar='-1', type=int, default=-1, help='which column in the sample metadata contains the AUC, default is the last')
    parser.add_argument('--count-start-col', metavar='1', type=int, default=1, help='which column in the raw coverage file start the counts')
    parser.add_argument('--sample-id-col', metavar='0', type=int, default=0, help='which column in the sample metadata contains the joining ID')
    parser.add_argument('--snaptron-format', action='store_const', const=True, default=False, help='if gene raw counts file is coming from the genes Snaptron formatted DB')
    parser.add_argument('--id-type', metavar='how to format the ID field', type=str, default='gene_id', help='what kind of row ID to use: "gene_id" (default), "coord"; only matters if --snaptron-format is also passed in')
    parser.add_argument('--skip-0-rows', action='store_const', const=True, default=False, help='if all normalized counts in a row are zeros, drop the row from output')
    args = parser.parse_args()

    if args.snaptron_format:
        args.count_start_col = 0

    (aucs, sids) = load_metadata(args)
    normalize_counts(args, aucs, sids)

if __name__ == '__main__':
    main()
