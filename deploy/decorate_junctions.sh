#!/bin/bash
#assumes bgzip is in PATH, dumps output to working directory
#reads from STDIN of raw tab-delimited junctions format: chr,start,end,strand,left_motif,right_motif,sample_id_list,sample_coverage_list
#plus 3 arguments required:
#1) full path to set of human genome reference-specific annotations to use to mark which junctions are known
#2) dataset ID (GTEx,SRA,TCGA,etc...)
#3) output name of BGZip file which decorated junctions will be written to for indexing by Tabix

#decorate the raw junctions with 1) annotations and 2) sample stats

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

#print header
perl -e 'print "".join("\t",("snaptron_id","chromosome","start","end","length","strand","annotated","left_motif","right_motif","left_annotated","right_annotated","samples","samples_count","coverage_sum","coverage_avg","coverage_median","compilation_id"))."\n";'

cat - | pypy ${p}/../annotations/process_introns.py --annotations ${1} | ${p}/compute_stats_per_record.sh ${2} | bgzip > ${3}
