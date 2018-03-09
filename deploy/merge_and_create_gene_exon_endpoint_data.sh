#!/bin/bash
#run the merge of the split gene/exon coverage TSV files, and then create Snaptron databases for the genes/exons endpoints

#1) argument is the name of compilation e.g. "supermouse", assumed to be the prefix of the coverage TSV files
#2) full path to annotation mapping gene_id/exon_id to genomic coordinates (e.g. gencode.v25.annotation.gff3.gz)
#3) full path to file containing sample metadata from Rail for this compilation (/data/snaptron_data/<compilation>/samples.tsv)
#4) source compilation ID (e.g. 2 for SRAv2)
#5) number of splits (usually 10 or 14)
#6) [optional] path to list of original disjoint exons from recount (e.g. recount_hg38_gencodev25_disjoint_exons.tsv)
#if this last is passed in, the fixup script will be run merge pre-run, artificially split exons (1000bp each)

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`
echo $p

perl -e 'for $a (("exons","genes")) { $i2=0; `head -1 /dataB/'${1}'.0.snapout.$a.tsv > ./'${1}'.all.$a`; for $i (66..(66+'${5}'-1)) { $i1=chr($i); `cat /data$i1/'${1}'.$i2.snapout.$a.tsv | grep -v start >> ./'${1}'.all.$a`; $i2++;}}'

if [[ $6 ]]; then
	#assumes snaptron server checkout also has the client checked out
	python ${p}/../client/scripts/fixup_gene_exon_bulk_base_intervals.py $6 ${1}.all.exons > ${1}.all.exons.fixed
	mv ${1}.all.exons.fixed ${1}.all.exons
fi

${p}/../deploy/decorate_genes_exons.sh ./${1}.all ${2} ${1} ${3} ${4}
