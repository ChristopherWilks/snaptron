#!/bin/bash
#run the merge of the split gene/exon coverage TSV files, and then create Snaptron databases for the genes/exons endpoints

#1) argument is the name of compilation e.g. "supermouse", assumed to be the prefix of the coverage TSV files
#2) full path to annotation mapping gene_id/exon_id to genomic coordinates (e.g. gencode.v25.annotation.gff3.gz)
#3) full path to file containing sample metadata from Rail for this compilation (/data/snaptron_data/<compilation>/samples.tsv)
#4) source compilation ID (e.g. 2 for SRAv2)
#5) number of splits (usually 10 or 14)

SUFFIX1='.0.snapout.'
SUFFIX2='.tsv'

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`
echo $p

perl -e 'for $a (("exons","genes")) { $i2=0; `head -1 /dataB/0.'${1}'.$a > ./'${1}'.all.$a`; for $i (66..(66+'${5}'-1)) { $i1=chr($i); `cat /data$i1/*.'${1}'.$a | grep -v start >> ./'${1}'.all.$a`; $i2++;}}'

${p}/../deploy/decorate_genes_exons.sh ./${1}.all ${2} ${1} ${3} ${4}
