#!/bin/bash

#from Lindenbaum's SQL on
#https://www.biostars.org/p/19029/
#echo 'select X.kgID,C.clusterId,R.* from kgXref as X,refGene as R,knownCanonical as C WHERE C.transcript=X.kgID and X.refseq=R.name and C.chromEnd=R.txEnd and C.chromStart=R.txStart' > t.sql

#loose (not coordinate matching), if more than one canonical transcript comes back, have the Perl one-liner filter based on transcript matching
echo 'select X.kgID,C.clusterId,C.chromStart,C.chromEnd,R.* from kgXref as X,refGene as R,knownCanonical as C WHERE C.transcript=X.kgID and X.refseq=R.name and C.chrom in ("chr1","chr2","chr3","chr4","chr5","chr6","chr7","chr8","chr9","chr10","chr11","chr12","chr13","chr14","chr15","chr16","chr17","chr18","chr19","chr20","chr21","chr22","chrX","chrY","chrM") and R.chrom=C.chrom;' > t.sql

mysql --user=genome --host=genome-mysql.cse.ucsc.edu -A -D hg19 < t.sql | perl -ne 'chomp; $s=$_; @f=split(/\t/,$s); $match=-1; $match=1 if($f[2] == $f[8] && $f[3] == $f[9]); if(!$h{$f[16]} || $h{$f[16]}->[1] == -1) { $h{$f[16]}=[$s,$match]; } END { for $a (values %h) { print "".$a->[0]."\n";}}' > hg19.ucsc_known_canonical.tsv

mysql --user=genome --host=genome-mysql.cse.ucsc.edu -A -D hg38 < t.sql | perl -ne 'chomp; $s=$_; @f=split(/\t/,$s); $match=-1; $match=1 if($f[2] == $f[8] && $f[3] == $f[9]); if(!$h{$f[16]} || $h{$f[16]}->[1] == -1) { $h{$f[16]}=[$s,$match]; } END { for $a (values %h) { print "".$a->[0]."\n";}}' > hg38.ucsc_known_canonical.tsv
