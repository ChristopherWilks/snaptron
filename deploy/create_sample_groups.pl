#!/usr/bin/perl
use strict;

#input is compilation specific samples.tsv

#my %col_map = ('tcga'=>[1,79,83,102],'gtex'=>[1,66,302],'srav2'=>[1,5,19]);
my %col_map = ('tcga'=>[0,78,82,101],'tcgav2'=>[0,78,82,101],'gtex'=>[1,66,302],'gtexv2'=>[0,12,13],'srav2'=>[1,5,19],'ccle'=>[0,7,4],'srav3h'=>[0,2,8],'srav1m'=>[0,2,8]);

my $type = shift;

my %h;
while(my $line = <STDIN>)
{
	chomp($line); 
	my @f=split(/\t/,$line);
	my @cols = @{$col_map{$type}};
    #skip any gtexv2 run which is either a K-562 cell line or is a tech rep
    #next if($type eq 'gtexv2' && ($f[2]=~/K-562/ || $f[2]!~/\.1$/));
    next if($type eq 'gtexv2' && $f[2]!~/\.1$/);
	my ($rid,$dcode,$dlong)=($f[$cols[0]],$f[$cols[1]],$f[$cols[2]]);
	
	$dlong=~s/\t/ /g;
	if($rid=~/rail_id/) 
	{ 
        #print "$dcode"."_tumor|normal\t$dlong\tnum_samples\trail_ids\n" if($type eq 'tcga');
        #print "$dcode\t$dlong\tnum_samples\trail_ids\n" if($type ne 'tcga'); 
		print "$dcode\t$dlong\tnum_samples\trail_ids\n" if($type ne 'tcga'); 
		next;
	} 
	$dcode=~s/TCGA-//; 
	$dcode=~s/CCLE-//; 
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

print "group_short_name\tgroup_long_name\trail_id_count\trail_ids\n";
for my $k (sort { $a cmp $b} keys %h) 
{ 
	my @v=@{$h{$k}}; 
	my $nsamps=scalar @{$v[0]};
    $k="NA" if($k =~ /^$/);
	print "$k\t".$v[1]."\t".$nsamps."\t".join(",",@{$v[0]})."\n";
}
