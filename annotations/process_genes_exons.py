#!/usr/bin/env python

import os
import sys
import gzip

gene_id_col_map={'exon':2,'gene':1}
def load_annotation(annot_type, annotation_file):
    gene2coords = {}
    gene2num_exons = {}
    #chr1    HAVANA  gene    11869   14409   .       +       .       ID=ENSG00000223972.5;gene_id=ENSG00000223972.5;gene_type=transcribed_unprocessed_pseudogene;gene_status=KNOWN;gene_name=DDX11L1;level=2;havana_gene=OTTHUMG00000000961.2
    with gzip.open(annotation_file,"rb") as f:
        for line in f:
            #skip comments
            if line[0] == '#':
                continue
            fields = line.rstrip().split('\t')
            #only need genes or exons
            #if genes we can also match exons since we need their count per gene
            if fields[2] != annot_type and (annot_type == 'exon' or fields[2] != 'exon'):
                continue
            #keep the 'chr' prefix, need for Tabix
            chrom=fields[0]
            (start,end,strand) = (fields[3],fields[4],fields[6])
            subfields=dict([x.split('=') for x in fields[8].split(';')])
            if fields[2] == 'exon' and annot_type == 'gene':
                if subfields['gene_id'] not in gene2num_exons:
                    gene2num_exons[subfields['gene_id']] = 0
                gene2num_exons[subfields['gene_id']]+=1
                continue
            gene2coords[subfields['gene_id']]=[chrom,start,end,strand,subfields['gene_name'],subfields['gene_type']]
    return (gene2coords, gene2num_exons)


sample_id_col_map={'srav2':1,'gtex':1,'tcga':23,'supermouse':0}
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
   
    (gene2coords, gene2num_exons) = load_annotation(args.annot_type, args.annotation)
    srr2ids = load_sample_id_map(args.sample_metadata, args.sample_source)

    snaptron_id = 0
    sample_id_mapping = {}
    sample_id_cols = []
    for line in sys.stdin:
        fields = line.strip().split('\t')
        if fields[0] == 'gene_id':
            for (i,sample) in enumerate(fields[3:]):
                if sample not in srr2ids:
                    sys.stderr.write("SAMPLE_NOT_PRESENT\t"+sample+"\t"+str(i+3)+"\n")
                    continue
                sample_id_mapping[i+3]=srr2ids[sample]
            continue
        gene_id = fields[0]
        bp_length = fields[1]
        symbol = fields[2]
        if gene_id not in gene2coords:
            sys.stderr.write("MISSING_GENE_ID\t"+gene_id+"\n")
            continue
        (chrom, start, end, strand, gene_name, gene_type) = gene2coords[gene_id]
        exon_count = gene2num_exons[gene_id]
        if exon_count == 0:
            sys.stderr.write("0_EXON_GENE\t"+gene_id+"\n")
            continue
        length = str((int(end )- int(start)) + 1)
        #need offset of 3 since we have gene_id,length, and symbol before the sample counts
        sample_ids = [sample_id_mapping[i] for i in xrange(3,len(fields)) if float(fields[i]) > 0 and i in sample_id_mapping]
        #skip any with no samples
        if len(sample_ids) == 0:
            continue
        #now join up the samples and their coverages and write out
        sys.stdout.write("\t".join([str(snaptron_id), chrom, start, end, length, strand, "", "", "", str(exon_count), ":".join([gene_id,gene_name,gene_type,bp_length]), ','.join(sample_ids),','.join([fields[i] for i in xrange(3,len(fields)) if float(fields[i]) > 0 and i in sample_id_mapping])])+"\n")
        snaptron_id+=1
