#!/bin/bash
#assumes bgzip is in PATH, dumps output to working directory
#reads from STDIN of raw tab-delimited genes/exon expression format: gene_id,bp_length,symbol,tab delimited list of summarized raw read counts for samples
#plus 3 arguments required:
#1) full path to annotation mapping gene_id/exon_id to genomic coordinates
#2) source compilation (GTEx,SRA,TCGA,etc...)
#3) full path to file containing sample metadata from Rail for this compilation (/data/snaptron_data/<compilation>/samples.tsv)
#4) source compilation ID (e.g. 2 for SRAv2)

#output format
#tab-delimited: snaptron_id,chr,start,end,length,strand,unused,unused,unused,unused,unused,sample_id_coverage_list,sample_count,coverage_sum,coverage_avg,coverage_median,data_source_id
#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

echo $p

#print header
perl -e 'print "".join("\t",("snaptron_id","chromosome","start","end","length","strand","NA","NA","NA","exon_count","gene_id:gene_name:gene_type:bp_length","samples","samples_count","coverage_sum","coverage_avg","coverage_median","compilation_id"))."\n";'

export db="genes.sqlite"
sqlite3 $db < ${p}/snaptron_schema.sql
mkfifo ./import

#this will sort the output by coordinate, but because the snaptron_id has already been assigned by process_genes_exons.py, it will not be in order
cat - | pypy ${p}/../annotations/process_genes_exons.py --annotation ${1} --sample-source ${2} --sample-metadata ${3} --annot-type gene | sort -t'	' -k2,2 -k3,3n -k4,4n | ${p}/compute_stats_per_record.sh ${4} | tee ./import | bgzip > ${2}.genes.tsv.bgz &

sqlite3 $db -cmd '.separator "\t"' ".import ./import intron"

sqlite3 $db < ${p}/snaptron_schema_index.sql
rm ./import
