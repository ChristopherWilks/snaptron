#!/bin/bash

egrep -v -e '^#' Homo_sapiens.GRCh37.75.gtf.sorted | perl -ne 'chomp; @f=split(/\t/,$_); if($f[0] =~ /^(\d+|M|Y|X)$/i) { $f[0]="chr".$f[0]; } $f[1]="ENSEMBL"; print "".(join("\t",@f))."\n";' > all_3_before_consolidation_sources.gtf

egrep -v -e '^#' gencode.v19.annotation.gtf.sorted | perl -ne 'chomp; @f=split(/\t/,$_); $f[1]="GENCODE"; print "".(join("\t",@f))."\n";' >> all_3_before_consolidation_sources.gtf

egrep -v -e '^#' refGene.gtf.sorted | perl -ne 'chomp; @f=split(/\t/,$_); $f[1]="REFGENE"; print "".(join("\t",@f))."\n";' >> all_3_before_consolidation_sources.gtf

sort -t' ' -s -k1,1 -k4,4n -k5,5n all_3_before_consolidation_sources.gtf > all_3_before_consolidation_sources.gtf.sorted

perl /data/gigatron/snaptron/scripts/consolidate_gene_annotation.pl all_3_before_consolidation_sources.gtf.sorted | sort -t'	' -s -k1,1 -k4,4n -k5,5n | gzip > gensemrefg.hg19_annotations.sorted.gtf.gz
