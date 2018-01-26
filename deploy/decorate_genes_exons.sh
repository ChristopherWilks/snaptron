#!/bin/bash
#assumes bgzip is in PATH, dumps output to working directory
#assumes summarization by Snaptron consolidated BigWig approach, not recount (so includes coordinates, no gene symbols)
#5 arguments required:
#1) path/prefix of files with raw tab-delimited genes and exon expression formatted: gene_id,bp_length,chrm,start,end,tab delimited list of summarized raw read counts for samples
#2) full path to annotation mapping gene_id/exon_id to genomic coordinates (e.g. gencode.v25.annotation.gff3.gz)
#3) source compilation (GTEx,SRA,TCGA,etc...)
#4) full path to file containing sample metadata from Rail for this compilation (/data/snaptron_data/<compilation>/samples.tsv)
#5) source compilation ID (e.g. 2 for SRAv2)

#output format
#tab-delimited: snaptron_id,chr,start,end,length,strand,unused,unused,unused,unused,unused,sample_id_coverage_list,sample_count,coverage_sum,coverage_avg,coverage_median,data_source_id
#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

echo $p

#print header
perl -e 'print "".join("\t",("snaptron_id","chromosome","start","end","length","strand","NA","NA","NA","exon_count","gene_id:gene_name:gene_type:bp_length","samples","samples_count","coverage_sum","coverage_avg","coverage_median","compilation_id"))."\n";'

#####GENES
export db="genes.sqlite"
rm ${db}
sqlite3 $db < ${p}/snaptron_schema.sql
mkfifo ./import

#this will sort the output by coordinate, but because the snaptron_id has already been assigned by process_genes_exons.py, it will not be in order
python ${p}/../annotations/process_genes_exons.py --counts-file ${1}.genes --annotation ${2} --sample-source ${3} --sample-metadata ${4} --annot-type gene --with-coords --as-ints | sort -t'	' -k2,2 -k3,3n -k4,4n | ${p}/compute_stats_per_record.sh ${5} | tee ./import | bgzip > ${3}.genes.tsv.bgz &
sqlite3 $db -cmd '.separator "\t"' ".import ./import intron"
sqlite3 $db < ${p}/snaptron_schema_index.sql
tabix -s2 -b3 -e4 ${3}.genes.tsv.bgz

#####EXONS
export db="exons.sqlite"
rm ${db}
sqlite3 $db < ${p}/snaptron_schema.sql

#this will sort the output by coordinate, but because the snaptron_id has already been assigned by process_genes_exons.py, it will not be in order
python ${p}/../annotations/process_genes_exons.py --counts-file ${1}.exons --annotation ${2} --sample-source ${3} --sample-metadata ${4} --annot-type exon --with-coords --as-ints | sort -t'	' -k2,2 -k3,3n -k4,4n | ${p}/compute_stats_per_record.sh ${5} | tee ./import | bgzip > ${3}.exons.tsv.bgz &
sqlite3 $db -cmd '.separator "\t"' ".import ./import intron"
sqlite3 $db < ${p}/snaptron_schema_index.sql
tabix -s2 -b3 -e4 ${3}.exons.tsv.bgz
rm ./import
