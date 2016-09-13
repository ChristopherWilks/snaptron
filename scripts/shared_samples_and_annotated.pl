#!/usr/bin/perl
use strict;

my $ANNOTATED_COL=7;
my $L_ANNOTATED_COL=10;
my $R_ANNOTATED_COL=11;
my $SAMPLES_COL=12;
my $SAMPLES_COV_COL=13;
my $SAMPLES_COUNT_COL=14;
my $SAMPLES_COV_SUM_COL=15;

my $dir = shift;
main();

sub main
{
	my @files = `ls $dir/*.1.tsv`;
	chomp(@files);
	for my $f (@files)
	{
		$f=~s/^(.+\/)//g;
		my ($g) = split(/\./,$f);
		my $second = "$g.2.tsv";
		process_splice_pairs($g,$f,$second);
	}
}

sub process_splice_pairs
{
	my $gene = shift;
	my $first = shift;
	my $second = shift;

	open(IN1,"<$dir/$first");
	open(IN2,"<$dir/$second");

	#step through each output file at same rate, matching samples_count ranking
	#while(my $line1=<IN1>,my $line2=<IN2>)
	my $line1 = <IN1>;
	my $line2 = <IN2>;
	{
		chomp($line1);
		chomp($line2);
		
		my @f1 = split(/\t/,$line1);
		my @f2 = split(/\t/,$line2);
		my $fully_annotated = 0;
		$fully_annotated = 1 if((length($f1[$ANNOTATED_COL]) > 1 || $f1[$ANNOTATED_COL] == 1) && (length($f2[$ANNOTATED_COL]) > 1 || $f2[$ANNOTATED_COL] == 1));

		my ($ss_count,$ss_percent1,$ss_percent2,$scov_sum1,$scov_sum2,$ssamples,$nssamples1,$nssamples2) = determine_shared_samples($f1[$SAMPLES_COL],$f2[$SAMPLES_COL],$f1[$SAMPLES_COV_COL],$f2[$SAMPLES_COV_COL]);
		my $annotated_info = join("\t",($f1[$L_ANNOTATED_COL],$f1[$R_ANNOTATED_COL],$f2[$L_ANNOTATED_COL],$f2[$R_ANNOTATED_COL]));
		my ($scov_avg1,$scov_avg2) = ($scov_sum1/$f1[$SAMPLES_COV_SUM_COL],$scov_sum2/$f2[$SAMPLES_COV_SUM_COL]);
		print "$gene\t$fully_annotated\t$ss_count\t".$f1[$SAMPLES_COUNT_COL]."\t".$f2[$SAMPLES_COUNT_COL]."\t$ss_percent1\t$ss_percent2\t$scov_sum1\t$scov_sum2\t$f1[$SAMPLES_COV_SUM_COL]\t$f2[$SAMPLES_COV_SUM_COL]\t$scov_avg1\t$scov_avg2\t$annotated_info\t$ssamples\t$nssamples1\t$nssamples2\n";
	}
	close(IN1);
	close(IN2);
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
	return ($count, $count/$count1, $count/$count2, $scov_sum1, $scov_sum2, join(",",(sort {$a<=>$b} @shared)), join(",",(sort {$a<=>$b} keys %s1)), join(",",(sort {$a<=>$b} keys %s2)));
}
