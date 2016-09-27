#!/usr/bin/env python2.7
import sys

TOP_X = 5

def process_tissues(fields,tissue_map):
    tissue_set = set()
    tissue_list = []
    for tissue in fields:
        (tissue,score) = tissue.split(":")
        gtex_tissue = tissue
        if tissue in tissue_map:
            gtex_tissue = tissue_map[tissue]
        if gtex_tissue == '?':
            continue
        tissue_set.add(gtex_tissue)
        tissue_list.append(gtex_tissue)
    return [tissue_set,tissue_list]

tissue_map = {}
with open("genetech_hg19_exons.tsv.tissue_sorted.uniq_tissues","r") as fin:
    for line in fin:
        (gtech_tissue,gtex_tissue) = line.rstrip().split("\t")
        tissue_map[gtech_tissue] = gtex_tissue

gtech_file = sys.argv[1]
gtex_file = sys.argv[2]

gtech_tissues = {}
gtech_validations = {}
with open(gtech_file, "r") as fin:
    for line in fin:
        fields = line.rstrip().split("\t")
        gene = fields[0]
        gtech_tissues[gene] = process_tissues(fields[3:], tissue_map)
        gtech_validations[gene]=[fields[1],fields[2]]        


with open(gtex_file, "r") as fin:
    sys.stdout.write("gene\tvalidated_by_RTPCR\tvalidated_by_resequencing\tfirst_tissue_matches?\tmatch_within_first_two?\ttop_x_matches\ttop_x_overlap_ratio\tfull_overlap_ratio\tgenentech_tissues\tgtex_tissues\n")
    for line in fin:
        fields = line.rstrip().split("\t")
        gene = fields[0]
        if gene == 'gene':
            continue
        tissues = fields[33]
        (gtissue_set,gtissue_list) = gtech_tissues[gene]
        gtissue_str = ";".join(gtissue_list)
        (tissue_set,tissue_list) = process_tissues(tissues.split(";"),tissue_map)
        tissue_str = ";".join(tissue_list)
        
        overlap_ratio = len(gtissue_set.intersection(tissue_set))/float(len(gtissue_set))
       
        top_x_count = 0
        gtop_x_set = set()
        top_x_set = set()
        top_x = min(TOP_X,min(len(gtissue_list),len(tissue_list)))
        for (i,tissue) in enumerate(gtissue_list):
            if i == top_x:
                break
            gtop_x_set.add(tissue)
            top_x_set.add(tissue_list[i])
            if tissue == tissue_list[i]:
                top_x_count+=1
        top_x_count = top_x_count/float(top_x)

        top_x_overlap_ratio = len(gtop_x_set.intersection(top_x_set))/float(top_x)

        top_1_matches = gtissue_list[0] == tissue_list[0]
        top_2_matches = False
        if len(gtissue_list) >= 2 and len(tissue_list) >= 2:
            top_2_matches = gtissue_list[0] == tissue_list[1] or gtissue_list[1] == tissue_list[0]
    
        sys.stdout.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (gene,gtech_validations[gene][0],gtech_validations[gene][1],top_1_matches,top_2_matches,str(top_x_count),str(top_x_overlap_ratio),str(overlap_ratio),gtissue_str,tissue_str))
