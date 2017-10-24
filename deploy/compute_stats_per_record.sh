#!/bin/bash
#take a stream of junction-like records (could be gene/exon expression)
#and calculate count, sum, average, and median of coverage over the samples per record
#and block gzip the output

#stream from STDIN format:
#tab-delimited: snaptron_id,chr,start,end,length,strand,annotated_status,left_motif,right_motif,left_annotated,right_annotated,sample_id_list,sample_coverage_list

#one argument:
#dataset ID (GTEx,SRA,TCGA,etc...)

cat - | perl -ne 'BEGIN {$data_source_id='${1}';} chomp; $s=$_; @f=split(/\t/,$s); @coverages=split(/,/,pop(@f)); @samples=split(/,/,pop(@f)); $sample_count=scalar @samples; $cov_count=scalar @coverages; $cov_sum=0; map { $cov_sum+=$_; } @coverages; $avg=$cov_sum/$cov_count; $median=-1; $m_=$cov_count/2; $m_=int($m_); @f2a=sort {$a<=>$b} @coverages; if(($cov_count % 2)==0) { $m2_=$cov_count/2; $m2_-=1; $median=($f2a[$m_]+$f2a[$m2_])/2; } else { $median=$f2a[$m_]; }  print "".join("\t",@f)."\t"; for $i (0..$sample_count-1) { print ",".$samples[$i].":".$coverages[$i]; } printf("\t$sample_count\t$cov_sum\t%.3f\t%.3f\t$data_source_id\n",$avg,$median);'
