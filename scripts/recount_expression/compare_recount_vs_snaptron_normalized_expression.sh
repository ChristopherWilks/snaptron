#!/bin/bash
#tests recount's normalized gene counts against snaptron for a specific compilation/gene
#should be the same
#parameters:
#1: Gencode gene ID ("ENSG00000000419.12")
#2: /path/filename to [b]gzipped snaptron normalized genes file (full TSV of counts, which contains at least the gene ID and the counts) ("/data/tcga/gene_coverage_normalized.tsv.bgz")
#3: /path/filename to recount RSE of the compilation ("/data/tcga/rse_gene.Rdata")

scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`

Rscript $scripts/extract_recount_normalized_gene_count.R $1 $3 ${1}.recount_normalized_counts
cut -d' ' -f 2 ${1}.recount_normalized_counts | sed -e 's/"//g' > ${1}.recount_normalized_counts.cut
zcat $2 | fgrep $1 | perl -ne 'chomp; for $a (split(/\t/,$_)) { print "$a\n";}' | sort > $1.lines.sorted
cat ${1}.recount_normalized_counts.cut | sort > $3.lines.sorted

diff $1.lines.sorted $3.lines.sorted > ${1}.diff

