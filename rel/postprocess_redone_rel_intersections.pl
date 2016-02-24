#!/usr/bin/perl

use strict;
use warnings;

my $iidsF = shift;
my $resultsF = shift;

main();

sub main
{
	my $iids = load_ids($iidsF);
	process_results($resultsF,$iids);
}

sub process_results
{
	my $file = shift;
	my $iids = shift;

	open(IN,"<$file");

	my $rels=0;
	my $srels=0;
	my %seen_sense;
	my %seen;
	my %by_sample;
	while(my $line = <IN>)
	{
		chomp($line);
		my ($cluster_id,$gname,$gstrand,$gstart,$gend,$rstart,$rend,$rstrand,$rname,$rtype,$coord_in_exon,$iid,$ichr,$istart,$iend,$LENGTH_TEMP,$istrand,$j1,$j2,$j3,$j4,$j5,$samples,$covs) = split(/\t/,$line);
		next if(!$iids->{$iid});
		next if($seen{$iid} && $seen_sense{$iid});
		my @samples = split(/,/,$samples);
		my $relsense = $gstrand eq $rstrand && $gstrand eq $istrand;
		$rels++ if(!$seen{$iid});
		$srels++ if($relsense && !$seen_sense{$iid});
		foreach my $sample (@samples)
		{
			$by_sample{$sample}->[0]++ if(!$seen{$iid});
			$by_sample{$sample}->[1]++ if($relsense && !$seen_sense{$iid});
		}
		$seen{$iid}=1;
		$seen_sense{$iid}=1 if($relsense);
	}
	foreach my $sample (keys %by_sample)
	{
		my ($rels,$srels) = @{$by_sample{$sample}};
		$srels = 0 if(!$srels);
		print "$sample\t$srels/$rels\n";
	}
	print "$srels/$rels\n";
}

sub load_ids
{
	my $file = shift;
	my %iids;
	open(IN,"<$file");
	while(my $line = <IN>)
	{
		chomp($line);
		$iids{$line}=1;
	}
	return \%iids;
}	
