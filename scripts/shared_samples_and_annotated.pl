#!/usr/bin/perl
use strict;
#produces summary info per exon (2 flanking JXs) including list of shared samples between flanking splice sites

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

main();

sub main
{
	my $strand_map = load_strands();
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
	map { $tissue_counts.=",".$_.":".$tissues{$_}.",".sprintf("%.3f",$tissues{$_}/$sample_count); } sort { $tissues{$b} <=> $tissues{$a} } keys %tissues;
	$tissue_counts=~s/^,//;
	return $tissue_counts;
}
		

sub load_strands
{
	open(IN,"<$strand_file");
	my %h;
	while(my $line=<IN>)
	{
		chomp($line);
		my ($g,$coords) = split(/\t/,$line);
		$g=~s/"//g;
		my ($chrom,$coord,$strand)=split(/:/,$coords);
		die "ERROR\t$g\tdifferent strands for same gene\n" if($h{$g} && $h{$g} ne $strand);
		$h{$g}=$strand;
	}
	close(IN);
	return \%h;
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

	open(IN1,"<$dir/$first");
	open(IN2,"<$dir/$second");

	#grab top (by samples_count) hit for both flanking splices and look at shared sample membership
	my $g = $gene;
	$g=~s/_\d$//;
	my $strand = $strand_map->{$g};
	my @f1;
	while(my $line1=<IN1>)
	{
		chomp($line1);
		@f1 = split(/\t/,$line1);
		last if($f1[$STRAND_COL] eq $strand);
	}
	my @f2;
	while(my $line2=<IN2>)
	{
		chomp($line2);
		@f2 = split(/\t/,$line2);
		last if($f2[$STRAND_COL] eq $strand);
	}
	close(IN1);
	close(IN2);
	die "ERROR\t$gene\tno strand matching junctions for both flanks, exiting\n" if(scalar @f1 == 0 || scalar @f2 == 0);
	
	my $fully_annotated = 0;
	$fully_annotated = 1 if((length($f1[$ANNOTATED_COL]) > 1 || $f1[$ANNOTATED_COL] == 1) && (length($f2[$ANNOTATED_COL]) > 1 || $f2[$ANNOTATED_COL] == 1));

	my ($ss_count,$ss_percent1,$ss_percent2,$scov_sum1,$scov_sum2,$ssamples,$nssamples1,$nssamples2) = determine_shared_samples($f1[$SAMPLES_COL],$f2[$SAMPLES_COL],$f1[$SAMPLES_COV_COL],$f2[$SAMPLES_COV_COL]);
	my $annotated_info = join("\t",($f1[$L_ANNOTATED_COL],$f1[$R_ANNOTATED_COL],$f2[$L_ANNOTATED_COL],$f2[$R_ANNOTATED_COL]));
	my ($scov_avg1,$scov_avg2) = (sprintf("%.3f",$scov_sum1/$f1[$SAMPLES_COV_SUM_COL]),sprintf("%.3f",$scov_sum2/$f2[$SAMPLES_COV_SUM_COL]));

	#if requested (only for GTEx) get the tissues for all shared samples
	my $tissues_shared = get_tissues($ssamples,$ss_count) if($get_tissues);
	my $tissues1 = get_tissues($nssamples1,$f1[$SAMPLES_COUNT_COL]-$ss_count) if($get_tissues);
	my $tissues2 = get_tissues($nssamples2,$f2[$SAMPLES_COUNT_COL]-$ss_count) if($get_tissues);

	print "$gene\t$fully_annotated\t$ss_count\t".$f1[$SAMPLES_COUNT_COL]."\t".$f2[$SAMPLES_COUNT_COL]."\t$ss_percent1\t$ss_percent2\t$scov_sum1\t$scov_sum2\t$f1[$SAMPLES_COV_SUM_COL]\t$f2[$SAMPLES_COV_SUM_COL]\t$scov_avg1\t$scov_avg2\t$tissues_shared\t$tissues1\t$tissues2\t$annotated_info\t$ssamples\t$nssamples1\t$nssamples2\n";
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
	for my $k (keys %s1)
	{
		if($s2{$k}>=1)
		{
			push(@shared,$k);
			$scov_sum1+=$covs1[$s1{$k}-1];
			$scov_sum2+=$covs2[$s2{$k}-1];
			delete $s1{$k};
			delete $s2{$k};
		}
	}
	my $count = scalar @shared;
	return ($count, sprintf("%.3f",$count/$count1), sprintf("%.3f",$count/$count2), $scov_sum1, $scov_sum2, join(",",(sort {$a<=>$b} @shared)), join(",",(sort {$a<=>$b} keys %s1)), join(",",(sort {$a<=>$b} keys %s2)));
}
