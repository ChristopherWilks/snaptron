#!/bin/bash
#take a stream of junction-like records (could be gene/exon expression)
#and calculate count, sum, average, and median of coverage over the samples per record
#and block gzip the output

#stream from STDIN format:
#tab-delimited: snaptron_id,chr,start,end,length,strand,annotated_status,left_motif,right_motif,left_annotated,right_annotated,sample_id:coverage(comma delimited),num_samples,total_sum_coverage

#one argument:
#dataset ID (GTEx,SRA,TCGA,etc...)

NUM_COLS_EXPECTED=14

cat - | perl -ne 'BEGIN {$data_source_id='${1}';} chomp; $s=$_; @f=split(/\t/,$s); if(scalar @f < '${NUM_COLS_EXPECTED}') { print STDERR $s."\n"; next; } $cov_sum=pop(@f); $sample_count=pop(@f); @samples=split(/,/,pop(@f)); shift(@samples); @coverages = map { $samp=$_; $samp=~s/^\d+:(\d+)$/$1/; $samp; } @samples; $avg=$cov_sum/$sample_count; $median=-1; $m_=$sample_count/2; $m_=int($m_); @f2a=sort {$a<=>$b} @coverages; if(($sample_count % 2)==0) { $m2_=$sample_count/2; $m2_-=1; $median=($f2a[$m_]+$f2a[$m2_])/2; } else { $median=$f2a[$m_]; } printf("$s\t%.3f\t%.3f\t$data_source_id\n",$avg,$median);'
