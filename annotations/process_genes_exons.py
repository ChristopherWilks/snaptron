#!/usr/bin/env python

import os
import sys
import gzip

gene_id_col_map={'exon':2,'gene':1}
def load_annotation(args, annot_type, annotation_file):
    gene2coords = {}
    gene2num_exons = {}
    #gene format:
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
            #if annot_type == 'exon' and args.monorail:
                #exon format:
                #chr1    HAVANA  exon    11869   12227   .       +       .       ID=exon:ENST00000456328.2:1;Parent=ENST00000456328.2;gene_id=ENSG00000223972.5;transcript_id=ENST00000456328.2;gene_type=transcribed_unprocessed_pseudogene;gene_name=DDX11L1;transcript_type=processed_transcript;transcript_name=DDX11L1-002;exon_number=1;exon_id=ENSE00002234944.1;level=2;transcript_support_level=1;tag=basic;havana_gene=OTTHUMG00000000961.2;havana_transcript=OTTHUMT00000362751.1
                #exon_id = subfields['exon_id']
                #subfields['gene_id'] = subfields['exon_id']
            gene2coords[subfields['gene_id']]=[chrom,start,end,strand,subfields['gene_name'],subfields['gene_type']]
    return (gene2coords, gene2num_exons)


sample_id_col_map={'srav2':1,'gtex':1, 'gtexv2':2, 'tcga':23, 'tcgav2':23, 'supermouse':0,'encode1159':0, 'srav3h':1, 'srav1m':1}
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
    #parser.add_argument('--counts-file', type=str, required=True,
    #        help='path to file with counts for genes/exons'
    #    )
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
    parser.add_argument('--with-coords', action='store_const', const=True, 
            default=False, help='input contains chrom,start,end per gene/exon')
    parser.add_argument('--as-ints', action='store_const', const=True, 
            default=False, help='convert all floating point to integers (if there is no non-0 decimal part)')
    parser.add_argument('--monorail', action='store_const', const=True, 
            default=False, help='handle gene/exon ids differently; allow for multiple gene_ids')

    args = parser.parse_args()
   
    (gene2coords, gene2num_exons) = load_annotation(args, args.annot_type, args.annotation)
    srr2ids = load_sample_id_map(args.sample_metadata, args.sample_source)

    snaptron_id = -1
    sample_id_mapping = {}
    sample_id_cols = []
    field_offset = 3
    field_offset_offset = 3
    current_gene_id = None
    exon_id = 1
    if args.with_coords:
        #no symbol was passed in if we also have coordinates
        field_offset += 2
    #if args.annot_type == 'exon' and args.monorail:
    #    field_offset += 1
    #    field_offset_offset = 5
    fin = None
    for line in sys.stdin:
        fields = line.strip().split('\t')
        #header row
        if snaptron_id == -1:
            for (i,sample) in enumerate(fields[field_offset:]):
                if sample[0:3] == 'SRR':
                    if sample not in srr2ids:
                        sys.stderr.write("%s:SAMPLE_NOT_PRESENT\t%s\t%s\n" % (args.annot_type,sample,str(i+field_offset)))
                        continue
                    sample_id_mapping[i+field_offset]=srr2ids[sample]
                else:
                    sample_id_mapping[i+field_offset]=sample
            snaptron_id = 0
            continue
        gene_id = fields[0]
        #all_genes = []
        bp_length = fields[1]
        if args.annot_type == 'exon':
            if args.monorail:
                gene_ids = gene_id.split(';')
                for gid in gene_ids:
                    if gid in gene2coords:
                        gene_id = gid
                        #if args.multigene:
                            #(chrom, start, end, strand, gene_name, gene_type) = gene2coords[gid]
                            #all_genes.append(gene_name
                        break 
                bp_length = fields[4] 
                exon_id = 1
            else: 
                if args.with_coords:
                    gene_id = gene_id.split(':')[0]
                if gene_id != current_gene_id:
                    exon_id = 1
        if gene_id not in gene2coords:
            sys.stderr.write("%s:MISSING_GENE_ID\t%s\n" % (args.annot_type,gene_id))
            continue
        current_gene_id = gene_id
        (chrom, start, end, strand, gene_name, gene_type) = gene2coords[gene_id]
        #start of sample counts, assuming a symbol was also passed in (ignored)
        if args.with_coords:
            #no symbol was passed in if we also have coordinates
            start_offset = field_offset-field_offset_offset
            end_offset = start_offset + 3
            (chrom, start, end) = fields[start_offset:end_offset]
        exon_count = exon_id
        #for genes we don't know the total number of disjoint exons, so print nothing
        if args.annot_type == 'gene' or args.monorail:
            exon_count = ""
        length = str((int(end)- int(start)) + 1)
        sample_ids = [sample_id_mapping[i] for i in xrange(field_offset,len(fields)) if float(fields[i]) > 0 and i in sample_id_mapping]
        #skip any with no samples
        sys.stdout.write("\t".join([str(snaptron_id), chrom, start, end, length, strand, "", "", "", str(exon_count), ":".join([gene_id,gene_name,gene_type,bp_length])]))
        if len(sample_ids) == 0:
            sys.stderr.write("%s: no samples with counts > 0\t%s\n" % (args.annot_type,gene_id))
            sys.stdout.write("\t\t\n")
        else:
            #now join up the samples and their coverages and write out
            sys.stdout.write("\t"+','.join(sample_ids)+"\t")
            if args.as_ints:
                sys.stdout.write(','.join([str(int(float(fields[i]))) for i in xrange(field_offset,len(fields)) if float(fields[i]) > 0 and i in sample_id_mapping])+"\n")
            else:
                sys.stdout.write(','.join([fields[i] for i in xrange(field_offset,len(fields)) if float(fields[i]) > 0 and i in sample_id_mapping])+"\n")
        snaptron_id+=1
        exon_id+=1
    #fin.close()
