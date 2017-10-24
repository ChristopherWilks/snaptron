#!/bin/bash
#prototype workflow for gene expression from BigWigs
#not intended to run as-is at this point

#$1 is number of parallel bwtool jobs to run

#generate gene annotation disjoint exon extents BED file:
recount_generate_gene_exon_expression_groups.R

#gather list of all per-sample BigWigs
find ./coverage_bigwigs -name "*.bw" | grep -v -E "\\.[ACGNT]\\.bw" | grep -v -E "unique|mean|median" > all_bigwigs

#generate a list of bwtool summing jobs, one per BigWig
cat all_bigwigs | perl -ne 'chomp; $s=$_; print "sh /home-1/cwilks3@jhu.edu/recount-website/sum.sh /home-1/cwilks3@jhu.edu/bwtool-1.0/bwtool /home-1/cwilks3@jhu.edu/scratch/jling/supermouse/Gencode-mm-v15.exons.bed /work-zfs/blangme2/langmead/rail-runs/supermouse/coverage_bigwigs/$s ./coverage 2>./$s.bw.err\n";' > bwtool_sum.jobs

module load parallel
parallel -j $1 < bwtool_sum.jobs

#consolidate all per sample summed counts into one TSV (samples.tsv is the Snaptron/Rail sample metadata file)
cut -f 1,2,3 samples.tsv | perl -ne 'BEGIN { $cmd=""; $i=0; `cut -f 1,2,3 SRP073200-SRR3370920.sum.tsv > all2.tsv`; } chomp; ($r,$srr,$srp)=split(/\t/,$_); next if($r=~/rail/); if(++$i % 61 == 0 && length($cmd) > 0) { `/bin/bash -c "paste all2.tsv $cmd > all2.tsv2"`; `mv all2.tsv2 all2.tsv`; $cmd=""; } $cmd.=" <(cut -f 4 $srp-$srr.sum.tsv)"; END { if(length($cmd) > 0) { `/bin/bash -c "paste all2.tsv $cmd > all2.tsv2"`; `mv all2.tsv2 all2.tsv`;} }'

mv all2.tsv disjoint_exon_expression.tsv

#sum to gene level
python summarize_disjoint_exon_counts_to_gene_level.py gene_groupings.tsv disjoint_exon_expression.tsv > gene_expression.tsv
