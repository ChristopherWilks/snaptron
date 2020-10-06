#!/bin/bash
#assumes bgzip is in PATH, dumps output to working directory
#assumes summarization by Snaptron consolidated BigWig approach, not recount (so includes coordinates, no gene symbols)
#6 arguments required:
#1) path/prefix of exon counts file with raw tab-delimited exons expression formatted: gene_id,bp_length,chrm,start,end,tab delimited list of summarized raw read counts for samples
#2) full path to annotation mapping gene_id/exon_id to genomic coordinates (e.g. gencode.v25.annotation.gff3.gz)
#3) source compilation (GTEx,SRA,TCGA,etc...)
#4) full path to file containing sample metadata from Rail for this compilation (/data/snaptron_data/<compilation>/samples.tsv)
#5) source compilation ID (e.g. 2 for SRAv2)
#6) path of snaptron specific header for counts files [optional]

#output format
#tab-delimited: snaptron_id,chr,start,end,length,strand,unused,unused,unused,unused,unused,sample_id_coverage_list,sample_count,coverage_sum,coverage_avg,coverage_median,data_source_id
#get this script's path
p=$(dirname $0)

echo $p

#use appropriately large temp directory
export LARGE_TMP=/data5/tmp

#print header
perl -e 'print "".join("\t",("snaptron_id","chromosome","start","end","length","strand","NA","NA","NA","exon_count","gene_id:gene_name:gene_type:bp_length","samples","samples_count","coverage_sum","coverage_avg","coverage_median","compilation_id"))."\n";'

#####EXONS
`perl -e 'print STDERR "now running exons\n";'`
export db="exons.sqlite"
rm -f ${db}
sqlite3 $db < ${p}/snaptron_schema.sql
rm -f ./import_exons
mkfifo ./import_exons
#
cmd="pigz --stdout -p 2 -d ${1}"
if [[ ! -z $6 ]]; then
    #get rid of original header in input file and replace with rail_id version
    cmd="cat <(cat $6) <(pigz --stdout -p 2 -d ${1} | tail -n+2)"
fi

export LC_ALL=C
#this will sort the output by coordinate, but because the snaptron_id has already been assigned by process_genes_exons.py, it will not be in order
eval $cmd | pypy ${p}/../annotations/process_genes_exons.py --annotation ${2} --sample-source ${3} --sample-metadata ${4} --annot-type exon --with-coords --as-ints --monorail | sort -T$LARGE_TMP -t'	' -k2,2 -k3,3n -k4,4n | ${p}/compute_stats_per_record.sh ${5} | tee ./import_exons | ~/bgzip > ${3}.exons.tsv.bgz &
#OR split into 2 commands for flexibility when dealing with *very* large inputs (e.g. SRAv3h exons):
#pigz --stdout -p 2 -d $1 2> run1 | sort --parallel 4 -T$LARGE_TMP -t'	' -k3,3 -k4,4n -k5,5n | pigz --fast -p3 > ${1}.sorted.gz
#mv $1 ${1}.bak ; ln -fs ${1}.sorted.gz $1
#eval $cmd | pypy ${p}/../annotations/process_genes_exons.py --annotation ${2} --sample-source ${3} --sample-metadata ${4} --annot-type exon --with-coords --as-ints --monorail | ${p}/compute_stats_per_record.sh ${5} | bgzip -@ 4 > /data6/${3}.exons.tsv.bgz
sqlite3 $db -cmd '.separator "\t"' ".import ./import_exons intron"
sqlite3 $db < ${p}/snaptron_schema_index.sql
~/tabix -s2 -b3 -e4 /data6/${3}.exons.tsv.bgz
rm -f ./import_exons
