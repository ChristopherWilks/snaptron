#!/usr/bin/env bash
set -exo pipefail

#chrom id (1,2,...,18,19,M,X,Y)
c=$1
pcat chr${c}.jxns2studies.gz | perl -ne 'chomp; $f=$_; ($j,$jid,$c,$s,$e,$o,$ns,$cov,$samples)=split(/\t/,$f,-1); print "$j\t$jid\t$c:$s-$e:$o\t$ns\t$cov\n"; @samps=split(/,/,$samples,-1); for $samp (@samps) { print "$j\t$jid\t$samp\n";}' | bgzip -@4 > chr${c}.jxn2studies.gz
tabix -s2 -b1 -e1 chr${c}.jxn2studies.gz
