#!/bin/bash

report='relevant_sample_md_fields.processed.tsv3'

#generates an artifact (but really the mai) file called 'sample_counts.tsv'
#python ../find_gene-rp_overlaps.py knownGene_28-Jun-2015.clusterid.tsv ucsc_repeatmasker_2015_12_22.bed.sorted.gtf.no_chr_prefix consolidated_gtex_junctions.tsv.extended.gz consolidated_gtex_junctions.tsv.extended.gz.by_sample_count_coverate.tsv > annotated_repeated_introns.strands.tsv 2>errors &

#trust GTEX metadata where pairing is concerned (even if spots != spots_with_mates and LibraryLayout is PAIRED)
cut -f 1,11,12,13,14,19-23,27,36,37,42-44,46-48 gtex_pheno_table.tsv | perl -ne 'chomp; ($srr,$spots,$bases,$spots_with_mates,$avgLength,$LibraryName,$LibraryStrategy,$LibrarySelection,$LibrarySource,$LibraryLayout,$Model,$ScientificName,$SampleName,$Sex,$Disease,$Tumor,$Analyte_Type,$Histological_Type,$Body_Site)=split(/\t/,$_); $read=join("\t",($spots,$bases,$avgLength,$LibraryLayout)); $instrument=$Model; $tissue=join("\t",($Analyte_Type,$Body_Site,$Histological_Type,$Tumor,$Sex,$Disease)); $library=join("\t",($LibraryStrategy,$LibrarySource,$LibrarySelection,$LibraryName)); $s=join("\t",($idx,$srr,$read,$instrument,$library,$tissue,$ScientificName,$SampleName)); print "$s\n"; $idx++;'  > ${report}

perl ../join_junction_and_sample_md.pl ${report} sample_counts.tsv | cut -f 1,2,4- > sample_counts.tsv.formatted_md.tsv

echo 'intropolis_sample_id	SRR	REL_Gene_Splice_Sense_Frac	Gene_Splice_Sense_Frac	REL_Splice_Sense_Frac	REL_Total_Frac	REL_Cov_Frac	REL_Spot_Frac	REL_Gene_Splice_Sense_Count	REL_count	Gene_Splice_Sense_Count	REL_Splice_Sense_Count	Total_count	Rel_Cov	Total_Cov	spots	bases	avg_read_length	paired	platform_model	library_strategy	library_source	library_selection	library_name	analyte_type	body_site	histological_type	tumor	sex	disease	scientific_name	sample_name' >gtex_sarven_REL_report_by_sample_counts.sorted.tsv
sort -k3,3rn -k4,4rn -k5,5rn -k6,6rn sample_counts.tsv.formatted_md.tsv >> gtex_sarven_REL_report_by_sample_counts.sorted.tsv

#these two numbers should match
#check header
head -1 gtex_sarven_REL_report_by_sample_counts.sorted.tsv | perl -ne 'chomp; @f=split(/\t/,$_); $len=scalar(@f); print "$len\n"; foreach $s (@f) { print "$s,";} print "\n";'
#check file
head -2 gtex_sarven_REL_report_by_sample_counts.sorted.tsv | tail -1 | perl -ne 'chomp; @f=split(/\t/,$_); $len=scalar(@f); print "$len\n"; foreach $s (@f) { print "$s,";} print "\n";'

#check fractions
cut -f 2 sample_counts.tsv | perl -ne 'chomp; $s=$_; ($s1,$s2) = split(/\//,$s); $d=$s1/$s2; print "$d\n"; $count1++ if($d >= 0.5); $count2++ if($d < 0.5); END { print STDERR "$count1 $count2\n";}' > /dev/null
cut -f 3 sample_counts.tsv | perl -ne 'chomp; $s=$_; ($s1,$s2) = split(/\//,$s); $d=$s1/$s2; print "$d\n"; $count1++ if($d >= 0.5); $count2++ if($d < 0.5); END { print STDERR "$count1 $count2\n";}' > /dev/null
cut -f 4 sample_counts.tsv | perl -ne 'chomp; $s=$_; ($s1,$s2) = split(/\//,$s); $d=$s1/$s2; print "$d\n"; $count1++ if($d >= 0.5); $count2++ if($d < 0.5); END { print STDERR "$count1 $count2\n";}' > /dev/null
