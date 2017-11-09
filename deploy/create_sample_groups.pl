#!/usr/bin/perl
use strict;

#input is compilation specific samples.tsv

my %col_map = ('tcga'=>[1,79,83,102],'gtex'=>[1,66,302],'srav2'=>[1,5,19]);

my %h;
while(my $line = <STDIN>)
{
	chomp($line); 
	my @f=split(/\t/,$line);
	my @cols = @{$col_map{$type}};
	my ($rid,$dcode,$dlong)=($f[$cols[0]],$f[$cols[1]],$f[$cols[2]]);
	
	my $dlong=~s/\t/ /g;
	if($rid=~/rail_id/) 
	{ 
		print "$dcode"."_tumor|normal\t$dlong\tnum_samples\trail_ids\n" if($type eq 'tcga');
		print "$dcode\t$dlong\tnum_samples\trail_ids\n" if($type ne 'tcga'); 
		next;
	} 
	$dcode=~s/TCGA-//; 
	$dcode=~s/ /_/g;
	my $key=$dcode; 
	if($type eq 'tcga')
	{
		my $tcode = int($f[$cols[3]]);
		my $t="tumor"; 
		$t="normal" if($tcode >=10);
		$key="$dcode"."_$t";
	}
	$h{$key}=[[],$dlong] if(!$h{$key});
	push(@{$h{$key}->[0]},$rid); 
}

for my $k (sort { $a cmp $b} keys %h) 
{ 
	my @v=@{$h{$k}}; 
	my $nsamps=scalar @{$v[0]}; 
	print "$k\t".$v[1]."\t".$nsamps."\t".join(",",@{$v[0]})."\n";
}
