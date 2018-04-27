#!/usr/bin/env python2.7
import sys
import argparse
import gzip
import clsnaputil

#assumes you already have the AUCs
#pulled out using:
#wiggletools print non_unique_base_coverage.bw.auc AUC non_unique_base_coverage.bw

RECOUNT_TARGET = 40 * 1000000

def load_metadata(args):
    with open(args.metadata_file,"rb") as fin:
        lines = fin.read()
        lines = lines.split('\n')
        fields = lines[1].split('\t')
        if lines[len(lines)-1] == '':
            lines.pop()
        if args.auc_col == -1:
            args.auc_col = len(fields) - 1 
        aucs = {x.split('\t')[args.sample_id_col]:x.split('\t')[args.auc_col] for x in lines}
        return aucs

def normalize_counts(args,aucs):
    with gzip.open(args.counts_file,"rb") as fin:
        #maps column position
        header={}
        for line in fin:
            fields = line.rstrip().split('\t')
            gene_id = fields[0]
            if gene_id == 'gene_id' or gene_id == 'Group':
                sys.stdout.write(line)
                header={i:x for (i,x) in enumerate(fields[args.count_start_col:])}
                continue
            fields = [int(clsnaputil.round_like_R((RECOUNT_TARGET * float(x))/float(aucs[header[i]]),0)) for (i,x) in enumerate(fields[args.count_start_col:])]
            sys.stdout.write(gene_id+"\t"+"\t".join(map(str,fields))+"\n")

def main():
    parser = argparse.ArgumentParser(description='Normalization of raw counts')
    parser.add_argument('--counts-file', metavar='/path/to/counts_file', type=str, default=None, help='path to a TSV file with matrix of counts')
    parser.add_argument('--metadata-file', metavar='/path/to/sample_metadata_file', type=str, default=None, help='path to a TSV file with the Snaptron sample metadata')
    parser.add_argument('--auc-col', metavar='-1', type=int, default=-1, help='which column in the sample metadata contains the AUC, default is the last')
    parser.add_argument('--count-start-col', metavar='1', type=int, default=1, help='which column in the raw coverage file start the counts')
    parser.add_argument('--sample-id-col', metavar='0', type=int, default=0, help='which column in the sample metadata contains the joining ID')
    args = parser.parse_args()

    aucs = load_metadata(args)
    normalize_counts(args,aucs)

if __name__ == '__main__':
    main()
