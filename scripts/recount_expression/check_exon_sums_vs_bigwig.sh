#!/bin/env bash

#e.g. /data/snaptron_data/tcga/exons.bgz
exon_sums=$1
#"human" or "mouse"
#CD99 (human) or Snap25 (mouse)
gene_to_check=$2
#e.g. /data/snaptron_data/tcga/samples.tsv
samples=$3

last_rid=`tail -1 $samples | cut -f 1`

~/bwtool_mine2/bwtool summary ../ct_h_s/cd99.coords.bed 71110.bw  /dev/stdout -fill=0 -with-sum -keep-bed -decimals=0 | cut -f1-3,10 > cd99.exon.sums.71110.bw.sums

zcat $exon_sums | fgrep "${gene_to_check}" | cut -f2-4,12 | perl -ne 'chomp; ($c,$s,$e,$i)=split(/\t/,$_); $s--; if($i=~/,'${last_rid}':(\d+)/) { $s1=$1; print "$c\t$s\t$e\t$s1\n"; } else { print "$c\t$s\t$e\t0\n"; }' > ${gene_to_check}.exon.sums
