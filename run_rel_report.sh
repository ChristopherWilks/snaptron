#!/bin/bash

report='relevant_sample_md_fields.processed.tsv3'

#generates an artifact (but really the mai) file called 'sample_counts.tsv'
python ./find_gene-rp_overlaps.py knownGene_28-Jun-2015.clusterid.tsv ucsc_repeatmasker_2015_12_22.bed.sorted.gtf.no_chr_prefix all_SRA_introns_ids_stats_length_annotated.tsv.gtf all_SRA_introns_ids_stats_length_annotated.tsv.gtf.by_sample_count_coverate.tsv > annotated_repeated_introns.strands.tsv 2> errors

cat ../all_illumina_sra_for_human_ids.tsv | perl -ne 'chomp; @f=split(/\t/,$_); $ri=$f[28]; $count=-1; $i=undef; for($ri=~/BASE_COORD:\s+(\d+)/g) { $count++; $i=$1; } $length="NA"; $paired=$f[26]; $paired=~s/ -.*$//; if($count>-1 && $paired =~ /PAIRED/) { $length=$i; }  if(($paired=~/PAIRED/ && $count==0) || ($paired!~/PAIRED/ && $count==1)) { $paired="NA"; } $read=join("\t",($f[11],$f[12],$length,$paired)); $library=join("\t",($f[23],$f[24],$f[25],$f[22])); $descr=$f[27]; $instrument=$f[31]; $instrument=~s/INSTRUMENT_MODEL: //; $tissue=join("\t",($f[69],$f[70],$f[71],$f[72],$f[73],$f[74])); $isid=$f[0]; $srr=$f[1]; $s=join("\t",($isid,$srr,$read,$instrument,$library,$tissue,$descr)); print "$s\n";' > ${report}

#perl join_junction_and_sample_md.pl ${report} sample_counts.tsv SRA_BrainList_w_iids.tsv.just_iids | cut -f 1-9,11- > sample_counts.tsv.formatted_md.tsv
perl join_junction_and_sample_md.pl ${report} sample_counts.tsv SRA_BrainList_w_iids.tsv.just_iids > sample_counts.tsv.formatted_md.tsv

#echo 'intropolis_sample_id	SRR	in_sarvens_samples	REL Sense Frac	REL Total Frac	REL Cov Frac	REL Spot Frac	RELSense/REL	REL/Total	RelCov/TotCov	spots	bases	read_length	paired	platform_parameters	library_strategy	library_source	library_selection	library_name	cell_type	tissue	cell_line	strain	age	disease	library_construction_protocol' >sra_sarven_REL_report_by_sample_counts.sorted.tsv
echo 'intropolis_sample_id	SRR	in_sarvens_samples	REL_Gene_Splice_Sense_Frac	Gene_Splice_Sense_Frac	REL_Splice_Sense_Frac	REL_Total_Frac	REL_Cov_Frac	REL_Spot_Frac	REL_Gene_Splice_Sense_Count	REL_count	Gene_Splice_Sense_Count	REL_count	REL_Splice_Sense_Count	REL_count	REL_count	Total_count	Rel_Cov	Total_Cov	spots	bases	read_length	paired	platform_parameters	library_strategy	library_source	library_selection	library_name	cell_type	tissue	cell_line	strain	age	disease	library_construction_protocol' >sra_sarven_REL_report_by_sample_counts.sorted.tsv
sort -k4,4rn -k3,3rn -k5,5rn -k6,6rn -k7,7rn sample_counts.tsv.formatted_md.tsv >> sra_sarven_REL_report_by_sample_counts.sorted.tsv

#these two numbers should match
#check header
head -1 sra_sarven_REL_report_by_sample_counts.sorted.tsv | perl -ne 'chomp; @f=split(/\t/,$_); $len=scalar(@f); print "$len\n"; foreach $s (@f) { print "$s,";} print "\n";'
#check file
head -2 sra_sarven_REL_report_by_sample_counts.sorted.tsv | tail -1 | perl -ne 'chomp; @f=split(/\t/,$_); $len=scalar(@f); print "$len\n"; foreach $s (@f) { print "$s,";} print "\n";'

#check fractions
cut -f 2 sample_counts.tsv | perl -ne 'chomp; $s=$_; ($s1,$s2) = split(/\//,$s); $d=$s1/$s2; print "$d\n"; $count1++ if($d >= 0.5); $count2++ if($d < 0.5); END { print STDERR "$count1 $count2\n";}' > /dev/null
cut -f 3 sample_counts.tsv | perl -ne 'chomp; $s=$_; ($s1,$s2) = split(/\//,$s); $d=$s1/$s2; print "$d\n"; $count1++ if($d >= 0.5); $count2++ if($d < 0.5); END { print STDERR "$count1 $count2\n";}' > /dev/null
cut -f 4 sample_counts.tsv | perl -ne 'chomp; $s=$_; ($s1,$s2) = split(/\//,$s); $d=$s1/$s2; print "$d\n"; $count1++ if($d >= 0.5); $count2++ if($d < 0.5); END { print STDERR "$count1 $count2\n";}' > /dev/null
