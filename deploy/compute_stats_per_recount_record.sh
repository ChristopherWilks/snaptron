#!/bin/bash
#take a stream of junction-like records (could be gene/exon expression)
#and calculate count, sum, average, and median of coverage over the samples per record

#stream from STDIN format:
#comma-delimited set of rail_id:coverages

#one argument:
#dataset ID (GTEx,SRA,TCGA,etc...)

cat - | perl -ne 'BEGIN {$data_source_id='${1}';} chomp; $s=$_; @samples=split(/,/,$s); $sample_count=scalar @samples; $cov_sum=0; @coverages=(); @new_samples=(); map { if($_ ne "0") { push(@new_samples,$_); ($rid,$cov)=split(/:/,$_); $cov_sum+=$cov; push(@coverages,$cov); } } @samples; $avg=$cov_sum/$sample_count; $median=-1; $m_=$sample_count/2; $m_=int($m_); @f2a=sort {$a<=>$b} @coverages; if(($sample_count % 2)==0) { $m2_=$sample_count/2; $m2_-=1; $median=($f2a[$m_]+$f2a[$m2_])/2; } else { $median=$f2a[$m_]; } print ",".join(",",@new_samples); printf("\t$sample_count\t$cov_sum\t%.3f\t%.3f\t$data_source_id\n",$avg,$median);'
