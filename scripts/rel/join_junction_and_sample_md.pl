#!/usr/bin/perl
use strict;
use warnings;

my $sample_mdsF = shift;
my $intron_countsF = shift;
my $sarven_iids = shift;

main();

sub main
{
	my $sids = load_ids($sarven_iids);
	my $sample_mds = load_sample_mds($sample_mdsF);
	join_and_format($intron_countsF,$sample_mds,$sids);
}

sub join_and_format
{
	my $file = shift;
	my $sample_mds = shift;
	my $sarven_iids = shift;
	
	open(IN,"<$file");
	#have the later scripts print out the header since we still have to sort
	#print "intropolis_sample_id\tSRR\tin_sarvens_samples\tREL Sense Frac\tREL Total Frac\tREL Cov Frac\tREL Spot Frac\tRELSense count\tREL count\tREL count\tTotal count\tRel Cov\tTotal Cov\tspots\tbases\tlength OR read_spec\tpaired\tplatform_parameters\tlibrary_strategy\tlibrary_source\tlibrary_selection\tlibrary_name\tcell_type\ttissue\tcell_line\tstrain\tage\tdisease\tlibrary_construction_protocol\n";
	while(my $line=<IN>)
	{
		chomp($line);
		my @fields = split(/\t/,$line);
		my $sid = shift @fields;
		my $in_sarvens = ($sarven_iids->{$sid}?1:0);
		my $md = $sample_mds->{$sid};
    my @mds = split(/\t/,$md);
    my $srr = shift @mds;
		$md = join("\t",@mds);
		my $spots = $mds[0];
		#my @fracs;
		print "$sid\t$srr\t$in_sarvens";
		my $rel_vs_spots=-1;
    my $original_nums = join("\t",@fields);
		$original_nums=~s/\//\t/g;
		foreach my $div (@fields)
		{
			my ($num,$den) = split(/\//,$div);
	    #push(@fracs,($num/$den));
	    my $frac=$num/$den;
			printf("\t%.3f",$frac);
			if($rel_vs_spots == -1 && $spots && $spots !~/e/)
			{
				$rel_vs_spots=$den/$spots;
			}
		}
		if($rel_vs_spots==-1)
		{
			print "\tNA";
		}
		else
		{
			printf("\t%.3f",$rel_vs_spots);
		}
		print "\t$original_nums\t$md\n";
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

sub load_ids
{
	my $file = shift;
  return {} if(!$file);
	my %hash;
	open(IN,"<$file");
	while(my $line = <IN>)
	{
		chomp($line);
		$hash{$line}=1;
	}
	return \%hash;
}
