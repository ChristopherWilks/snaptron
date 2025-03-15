#!/usr/bin/env bash
set -exo pipefail

#chrom id (1,2,...,18,19,M,X,Y)
c=$1
#pcat chr${c}.jxns2studies.gz | perl -ne 'chomp; $f=$_; ($j,$jid,$c,$s,$e,$o,$ns,$cov,$samples)=split(/\t/,$f,-1); print "$j\t$jid\t$c:$s-$e:$o\t$ns\t$cov\n"; @samps=split(/,/,$samples,-1); for $samp (@samps) { print "$j\t$jid\t$samp\n";}' | bgzip -@4 > chr${c}.jxn2studies.gz
#tabix -s2 -b1 -e1 chr${c}.jxn2studies.gz
#pcat chr${c}.jxns2studies.gz | perl -ne 'chomp; $f=$_; ($j,$jid,$c,$s,$e,$o,$ns,$cov,$samples)=split(/\t/,$f,-1); print "$c\t$s\t$e\t$o\t$jid\t$ns\t$cov\n"; @samps=split(/,/,$samples,-1); for $samp (@samps) { print "$j\t$jid\t$samp\n";}' | bgzip -@4 > chr${c}.jxn2studies.gz
#pcat chr${c}.jxns2studies.gz | LC_ALL=C sort --parallel=4 -t$'\t' --stable -k2,2 -k3,3n -k4,4n | bgzip -@4 > chr${c}.jxn2studies.coords.gz
pcat chr${c}.jxns2studies.gz 2>{i}.recompress_run | bgzip -@4 > chr${c}.jxn2studies.gz
tabix -s3 -b4 -e5 chr${c}.jxn2studies.coords.gz
