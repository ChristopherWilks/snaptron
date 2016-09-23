#!/usr/bin/perl
use strict;
#produces summary info per exon (2 flanking JXs) including list of shared samples between flanking splice sites

my $MAX_INT=(2**32)-1;
my $CHROM_COL=2;
my $START_COL=3;
my $END_COL=4;
my $STRAND_COL=6;
my $ANNOTATED_COL=7;
my $L_ANNOTATED_COL=10;
my $R_ANNOTATED_COL=11;
my $SAMPLES_COL=12;
my $SAMPLES_COV_COL=13;
my $SAMPLES_COUNT_COL=14;
my $SAMPLES_COV_SUM_COL=15;

my $dir = shift;
my $strand_file = shift;
my $get_tissues = shift;
my $create_jir = shift;

main();

sub main
{
	my $top_info_h = "total_coverage\ttotal_cov_avg\ttotal_cov_median";
	my $shared_info_h = "all_shared_samples_count\tall_shared_samples_cov_sum\tall_shared_samples_cov_min_sum\tall_shared_samples_cov_avg\tall_shared_cov_median";
	my $annotated_info_h = "annotations_left_left\tannotations_left_right\tannotations_right_left\tannotations_right_right";
	my $additional_info_h = "JIR	groupA_count	groupB_count	validated_by_RTPCR	validated_by_resequencing";

	print "gene\texon_length\tleft_intron_length\tright_intron_length\tnum_junctions1\tnum_junctions2\tfully_annotated\t$shared_info_h\t$top_info_h\tshared_samples_count\tleft_samples_count\tright_samples_count\tleft_shared_samples_ratio\tright_shared_samples_ratio\tshared_samples_cov_sum_left\tshared_samples_cov_sum_right\tsamples_cov_sum_left\tsamples_cov_sum_right\tshared_samples_cov_avg_left\tshared_samples_cov_avg_right\tnum_tissues\tmax_tissues_ratio\t$additional_info_h\ttissues_shared\ttissues_left\ttissues_right\t$annotated_info_h\tshared_samples\tnon_shared_samples_left\tnon_shared_samples_right\n";

	my $strand_map = load_strand_and_JIR_and_validations();
	my @files = `ls $dir/*.1.tsv`;
	chomp(@files);
	for my $f (@files)
	{
		$f=~s/^(.+\/)//g;
		$f=~/^(.+)\.\d+\.tsv$/;
		my $g = $1;
		my $second = "$g.2.tsv";
		process_splice_pairs($g,$f,$second,$strand_map);
	}
}

#only for GTEx
sub get_tissues
{
	my $sample_ids = shift;
	my $sample_count = shift;

	return "" if($sample_count == 0);

	$sample_ids =~s/,$//;
	$sample_ids=~s/,/","/g;
	$sample_ids='"'.$sample_ids.'"';
	
	my %tissues;
	open(OUT1,">log");
	print OUT1 "[$sample_ids]";
	close(OUT1);
	open(INP,"-|","curl --data 'fields=[{\"ids\":[$sample_ids]}]' http://stingray.cs.jhu.edu:8090/gtex/samples | cut -f 2,66,67");
	while(my $row = <INP>)
	{
		chomp($row);
		next if($row =~ /intropolis/);
		my ($rail_id,$tumor_type,$tissue) = split(/\t/,$row);
		$tissues{"$tumor_type-$tissue"}++;
	}
	close(INP);
	my $tissue_counts="";
	my $max_tissues_ratio;
	map { $tissue_counts.=",".$_.":".$tissues{$_}.",".sprintf("%.3f",$tissues{$_}/$sample_count); $max_tissues_ratio = sprintf("%.3f",$tissues{$_}/$sample_count) if(!$max_tissues_ratio); } sort { $tissues{$b} <=> $tissues{$a} } keys %tissues;
	$tissue_counts=~s/^,//;
	return ($tissue_counts,scalar keys %tissues,$max_tissues_ratio);
}
		

sub load_strand_and_JIR_and_validations
{
	open(IN,"<$strand_file");
	my %h;
	while(my $line=<IN>)
	{
		chomp($line);
		my ($g,$coords,$jir,$groupA_count,$groupB_count,$vRTPCR,$vResequenceing) = split(/\t/,$line);
		$jir = sprintf("%.3f",$jir);
		$g=~s/"//g;
		my ($chrom,$coord,$strand)=split(/:/,$coords);
		die "ERROR\t$g\tdifferent strands for same gene\n" if($h{$g} && $h{$g}->[0] ne $strand);
		$h{$g}=[$strand,"$jir\t$groupA_count\t$groupB_count\t$vRTPCR\t$vResequenceing"];
	}
	close(IN);
	return \%h;
}

sub min
{
	my $value1=shift;
	my $value2=shift;

	return ($value1>$value2?$value2:$value1);
}

sub process_splice_pairs
{
	my $gene = shift;
	my $first = shift;
	my $second = shift;
	my $strand_map = shift;

	my @s1=stat("$dir/$first");
	my @s2=stat("$dir/$second");
	return if($s1[7] == 0 || $s2[7] == 0);

	#grab top (by samples_count) hit for both flanking splices and look at shared sample membership
	my $g = $gene;
	$g=~s/_\d$//;
	next if(!$strand_map->{$g});
	my ($strand,$jir_and_validations) = @{$strand_map->{$g}};

	my %all_samples1;
	my ($start1,$end1,$num_jxs1,$f1,$j1) = process_junctions("$dir/$first",\%all_samples1,$strand,$L_ANNOTATED_COL);
	my %all_samples2;
	my ($start2,$end2,$num_jxs2,$f2,$j2) = process_junctions("$dir/$second",\%all_samples2,$strand,$R_ANNOTATED_COL);
	#die "ERROR\t$gene\tno strand matching junctions for both flanks, exiting\n" if(scalar !($f1) || scalar !($f2));
	die "ERROR\t$gene\tno strand matching junctions for both flanks, exiting\n" if(scalar @$f1 == 0 || scalar @$f2 == 0);
	
	my @f1 = @$f1;
	my @f2 = @$f2;

	my $all_shared_samples_count = 0;
	my @all_shared_samples_covs;
	my @all_shared_samples_covs_mins;
	map { if($all_samples2{$_}) { $all_shared_samples_count++; push(@all_shared_samples_covs, ($all_samples2{$_} * $all_samples1{$_})); push(@all_shared_samples_covs_mins, min($all_samples2{$_}, $all_samples1{$_}));}} keys %all_samples1;
	my $all_shared_samples_cov_sum=0;
	my $all_shared_samples_cov_min_sum=0;
	map { $all_shared_samples_cov_sum+=$_; } @all_shared_samples_covs;
	map { $all_shared_samples_cov_min_sum+=$_; } @all_shared_samples_covs_mins;
	my ($all_shared_samples_cov_avg, $all_shared_samples_cov_median) = average_and_median_sample_coverage(\@all_shared_samples_covs);


	my $intron_length1 = ($end1-$start1)+1;
	my $intron_length2 = ($end2-$start2)+1;
	my $exon_length = ($start2-1)-($end1+1)+1;
	my $fully_annotated = 0;
	$fully_annotated = 1 if((length($f1[$ANNOTATED_COL]) > 1 || $f1[$ANNOTATED_COL] == 1) && (length($f2[$ANNOTATED_COL]) > 1 || $f2[$ANNOTATED_COL] == 1));

	#get coordinates for JIR calculation
	create_JIR_query_file($gene,$j1,$j2) if($get_tissues >= 2 || $create_jir);

	#print "$gene ".$f1[$SAMPLES_COL]." ".$f2[$SAMPLES_COL]."\n";
	my ($ss_count,$ss_percent1,$ss_percent2,$total_cov,$cov_avg,$cov_median,$scov_sum1,$scov_sum2,$ssamples,$nssamples1,$nssamples2) = determine_shared_samples($f1[$SAMPLES_COL],$f2[$SAMPLES_COL],$f1[$SAMPLES_COV_COL],$f2[$SAMPLES_COV_COL]);
	my $annotated_info = join("\t",($f1[$L_ANNOTATED_COL],$f1[$R_ANNOTATED_COL],$f2[$L_ANNOTATED_COL],$f2[$R_ANNOTATED_COL]));
	my ($scov_avg1,$scov_avg2) = (sprintf("%.3f",$scov_sum1/$f1[$SAMPLES_COV_SUM_COL]),sprintf("%.3f",$scov_sum2/$f2[$SAMPLES_COV_SUM_COL]));

	#if requested (only for GTEx) get the tissues for all shared samples
	my ($tissues_shared,$num_tissues,$max_tissues_ratio) = get_tissues($ssamples,$ss_count) if($get_tissues==1);
	my ($tissues1) = get_tissues($nssamples1,$f1[$SAMPLES_COUNT_COL]-$ss_count) if($get_tissues==1);
	my ($tissues2) = get_tissues($nssamples2,$f2[$SAMPLES_COUNT_COL]-$ss_count) if($get_tissues==1);


	my $top_info = join("\t",($total_cov,$cov_avg,$cov_median));
	my $shared_info = join("\t",($all_shared_samples_count,$all_shared_samples_cov_sum,$all_shared_samples_cov_min_sum,$all_shared_samples_cov_avg,$all_shared_samples_cov_median));

	print "$gene\t$exon_length\t$intron_length1\t$intron_length2\t$num_jxs1\t$num_jxs2\t$fully_annotated\t$shared_info\t$top_info\t$ss_count\t".$f1[$SAMPLES_COUNT_COL]."\t".$f2[$SAMPLES_COUNT_COL]."\t$ss_percent1\t$ss_percent2\t$scov_sum1\t$scov_sum2\t$f1[$SAMPLES_COV_SUM_COL]\t$f2[$SAMPLES_COV_SUM_COL]\t$scov_avg1\t$scov_avg2\t$num_tissues\t$max_tissues_ratio\t$jir_and_validations\t$tissues_shared\t$tissues1\t$tissues2\t$annotated_info\t$ssamples\t$nssamples1\t$nssamples2\n";

	#print "$gene\t$fully_annotated\t$ss_count\t".$f1[$SAMPLES_COUNT_COL]."\t".$f2[$SAMPLES_COUNT_COL]."\t$ss_percent1\t$ss_percent2\t$scov_sum1\t$scov_sum2\t$f1[$SAMPLES_COV_SUM_COL]\t$f2[$SAMPLES_COV_SUM_COL]\t$scov_avg1\t$scov_avg2\t$tissues_shared\t$tissues1\t$tissues2\t$annotated_info\t$ssamples\t$nssamples1\t$nssamples2\n";
}

sub process_junctions
{
	my $file = shift;
	my $samplesH = shift;
	my $strand = shift;
	my $annot_col = shift;

	open(IN1,"<$file");
	my @f1;
	my @jir;
	my $jir_intron_length=$MAX_INT;

	my ($start,$end);
	my $num_jxs = 0;
	while(my $line1=<IN1>)
	{
		chomp($line1);
		my @f1_ = split(/\t/,$line1);
		if($f1_[$STRAND_COL] eq $strand)
		{
			$num_jxs++;
			
			my @samples = split(/,/,$f1_[$SAMPLES_COL]);
			my @covs = split(/,/,$f1_[$SAMPLES_COV_COL]);
			my $i=0;
			#slight change sum over all coverage values across all junctions which share this splice 
			#AND have a compatible strand
			map { $samplesH->{$_}+=$covs[$i++]; } @samples;
			#only grab the top sample count junction that is compatible
			if(scalar @f1 == 0)
			{
				($start,$end) = ($f1_[$START_COL],$f1_[$END_COL]);
				@f1 = split(/\t/,$line1);
			}
			#determine if this is the flanking junction to use for the JIR
			my $intron_length = ($f1_[$END_COL]-$f1_[$START_COL])+1;
			if($f1_[$annot_col] ne "0" && $intron_length < $jir_intron_length)
			{
				@jir = @f1_;
				$jir_intron_length = $intron_length;
			}
		}
	}
	close(IN1);
	return ($start,$end,$num_jxs,\@f1,\@jir);
}



sub create_JIR_query_file
{
	my $g = shift;
	my $f1=shift;
	my $f2=shift;

	return if(scalar @$f1 == 0 || scalar @$f2 == 0);

	my $shared_samples_count = 0;
	my %samples1;
	map { $samples1{$_}=1; } split(/,/,$f1->[$SAMPLES_COL]);
	map { $shared_samples_count++ if($samples1{$_}); } split(/,/,$f2->[$SAMPLES_COL]);

	#the check for at least one co-occurring sample in both flanking introns for the JIR
	return if($shared_samples_count == 0);

	my ($chrom,$s1,$e1) = ($f1->[$CHROM_COL],$f1->[$START_COL],$f1->[$END_COL]);
	my ($chrom2,$s2,$e2) = ($f2->[$CHROM_COL],$f2->[$START_COL],$f2->[$END_COL]);
	my ($s11,$e22) = ($s1,$e2);

	open(OUT,">jir_hg38/$g.tsv");
	print OUT "region\texact\tthresholds\tgroup\n";
	print OUT "$chrom:$s1-$e1\t1\t\tgroupB\n";	
	print OUT "$chrom:$s2-$e2\t1\t\tgroupB\n";	
	print OUT "$chrom:$s11-$e22\t1\tannotated=1\tgroupA\n";
	close(OUT);
}


sub determine_shared_samples
{
	my $samples1 = shift;
	my $samples2 = shift;
	my $covs1 = shift;
	my $covs2 = shift;

	my @covs1 = split(/,/,$covs1);
	my @covs2 = split(/,/,$covs2);

	my %s1;
	my $scov_sum1=0;
	my %s2;
	my $scov_sum2=0;

	my $sidx=0;
	map { $s1{$_}=++$sidx; } split(/,/,$samples1);
	$sidx=0;
	map { $s2{$_}=++$sidx; } split(/,/,$samples2);

	my $count1 = scalar (keys %s1);
	my $count2 = scalar (keys %s2);

	my @shared;
	my @shared_covs;
	my $total_cov=0;
	for my $k (keys %s1)
	{
		if($s2{$k}>=1)
		{
			push(@shared,$k);
			$scov_sum1+=$covs1[$s1{$k}-1];
			$scov_sum2+=$covs2[$s2{$k}-1];
			my $cov = $covs1[$s1{$k}-1] + $covs2[$s2{$k}-1];
			push(@shared_covs,$cov);
			$total_cov+=$cov;
			delete $s1{$k};
			delete $s2{$k};
		}
	}
	my ($avg_cov, $median_cov) = average_and_median_sample_coverage(\@shared_covs);
	my $count = scalar @shared;
	return ($count, sprintf("%.3f",$count/$count1), sprintf("%.3f",$count/$count2), $total_cov, $avg_cov, $median_cov, $scov_sum1, $scov_sum2, join(",",(sort {$a<=>$b} @shared)), join(",",(sort {$a<=>$b} keys %s1)), join(",",(sort {$a<=>$b} keys %s2)));
}

sub average_and_median_sample_coverage
{
	my $shared_covs = shift;

	my @shared_covs = @$shared_covs;
	return (-1,-1) if(scalar @shared_covs == 0);
	my @t = sort {$a <=> $b} @shared_covs;
	my $avg_cov=0;
	map {$avg_cov+=$_;} @shared_covs;
	$avg_cov = $avg_cov/(scalar @shared_covs);
	my $median_idx = int((scalar @t)/2);
	my $median_cov = ($median_idx != (scalar @t)/2?$t[$median_idx]:(($t[$median_idx]+$t[$median_idx-1])/2));
	return (sprintf("%.3f",$avg_cov), $median_cov);
}
