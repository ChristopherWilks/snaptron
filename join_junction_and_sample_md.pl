#!/usr/bin/perl
use strict;
use warnings;

my $sample_mdsF = shift;
my $intron_countsF = shift;

main();

sub main
{
	my $sample_mds = load_sample_mds($sample_mdsF);
	join_and_format($intron_countsF,$sample_mds);
}

sub join_and_format
{
	my $file = shift;
	my $sample_mds = shift;
	
	open(IN,"<$file");
	while(my $line=<IN>)
	{
		chomp($line);
		my @fields = split(/\t/,$line);
		my $sid = shift @fields;
		my $md = $sample_mds->{$sid};
                my @mds = split(/\t/,$md);
		my $spots = $mds[0];
		#my @fracs;
		print "$sid";
		my $rel_vs_spots=-1;
		foreach my $div (@fields)
		{
			my ($num,$den) = split(/\//,$div);
		        #push(@fracs,($num/$den));
		        my $frac=$num/$den;
			printf("\t%.3f",$frac);
			if($rel_vs_spots == -1 && $spots)
			{
				$rel_vs_spots=$den/$spots;
			}
		}
		printf("\t%.3f",$rel_vs_spots);
		print "\t$md\n";
	}
	close(IN);
}

	

sub load_sample_mds
{
	my $file = shift;
	open(IN,"<$file");
	my %hash;
	while(my $line=<IN>)
	{
		chomp($line);
		my @fields = split(/\t/,$line);
		my $sid = shift @fields;
		$hash{$sid}=join("\t",@fields);
	}
	close(IN);
	return \%hash;
}
