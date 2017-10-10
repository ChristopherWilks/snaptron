#!/usr/bin/env python

import os
import sys
import gzip

gene_id_col_map={'exon':2,'gene':1}
def load_annotation(annot_type, annotation_file):
    gene2coords = {}
    #chr1    HAVANA  gene    11869   14409   .       +       .       ID=ENSG00000223972.5;gene_id=ENSG00000223972.5;gene_type=transcribed_unprocessed_pseudogene;gene_status=KNOWN;gene_name=DDX11L1;level=2;havana_gene=OTTHUMG00000000961.2
    with gzip.open(annotation_file,"rb") as f:
        for line in f:
            #skip comments
            if line[0] == '#':
                continue
            fields = line.rstrip().split('\t')
            #only need genes or exons
            if fields[2] != annot_type:
                continue
            #keep the 'chr' prefix, need for Tabix
            chrom=fields[0]
            (start,end,strand) = (fields[3],fields[4],fields[6])
            subfields = fields[8].split(';')
            (junk,gene_id) = subfields[gene_id_col_map[annot_type]].split('=')
            gene2coords[gene_id]=[chrom,start,end,strand]
    return gene2coords

sample_id_col_map={'srav2':1,'gtex':1,'tcga':23}
def load_sample_id_map(sample_file, source):
    #we want the SRR accession2rail_id mapping
    sample2ids = {}
    sample_id_col = sample_id_col_map[source]
    with open(sample_file,'rb') as fin:
        for line in fin:
            fields = line.rstrip().split('\t')
            sample2ids[fields[sample_id_col].upper()]=fields[0]
    return sample2ids


if __name__ == '__main__':
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('--annotation', type=str, required=True,
            help='path to GTF file of annotation used to produce input gene/exon expressions'
        )
    parser.add_argument('--annot-type', type=str, required=True,
            help='"gene" or "exon"'
        )
    parser.add_argument('--sample-metadata', type=str, required=True,
            help='path to GTF file of full metadata fields for samples'
        )
    parser.add_argument('--sample-source', type=str, required=True,
            help='name of source compilation: "srav2", "gtex", or "tcga"'
        )
    args = parser.parse_args()
   
    gene2coords = load_annotation(args.annot_type, args.annotation)
    srr2ids = load_sample_id_map(args.sample_metadata, args.sample_source)

    snaptron_id = 0
    sample_id_mapping = []
    for line in sys.stdin:
        fields = line.strip().split('\t')
        if fields[0] == 'gene_id':
            sample_id_mapping = [srr2ids[sample] for sample in fields[3:]]
            continue
        gene_id = fields[0]
        bp_length = fields[1]
        symbol = fields[2]
        if gene_id not in gene2coords:
            sys.stderr.write("MISSING_GENE_ID\t"+gene_id+"\n")
            continue
        (chrom, start, end, strand) = gene2coords[gene_id]
        length = str((int(end )- int(start)) + 1)
        #need offset of 3 since we have gene_id,length, and symbol before the sample counts
        sample_ids = [sample_id_mapping[i-3] for i in xrange(3,len(fields)) if float(fields[i]) > 0]
        #now join up the samples and their coverages and write out
        sys.stdout.write("\t".join([str(snaptron_id), chrom, start, end, length, strand, "", "", "", gene_id, symbol, ','.join(sample_ids),','.join([fields[i+3] for i in xrange(0,len(sample_ids))])])+"\n")
        snaptron_id+=1
