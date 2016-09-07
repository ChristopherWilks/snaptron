#!/usr/bin/perl
use strict;

my $CHAINS={'hg38'=>'hg19ToHg38.over.chain.gz','hg19'=>'hg38ToHg19.over.chain.gz'};

my $file = shift;
#target reference
my $ref = shift;

$ref='hg38' if(!$ref);
my $liftover_chain_file = $CHAINS->{$ref};

my ($header,$lines);

open(IN,"<$file");
open(OUT,">$file.bed");
while(my $line=<IN>)
{
	chomp($line);
	if($line =~/region/)
	{
		$header = $line;
		next;
	}
	my @f = split(/\t/,$line);
	my $region = shift @f;
	if($region =~ /^(chr[1-9MXY]{1,2}):(\d+)-(\d+)$/)
	{
		my $chr=$1;
		my $start=$2;
		my $end=$3;
		print OUT "$chr\t$start\t$end\t$file\n";
		$line = join("\t",@f);
		push(@{$lines},$line);
	}
}
close(IN);
close(OUT);

print "running ./liftover $file.bed $liftover_chain_file $file.bed.liftedover.$ref unmapped\n";
`./liftover -minMatch=1.00 -ends=2 $file.bed $liftover_chain_file $file.bed.liftedover.$ref unmapped`;

open(IN,"<$file.bed.liftedover.$ref");
open(OUT,">$file.$ref");

print OUT "$header\n";
my $idx=0;
while(my $line=<IN>)
{
	chomp($line);
	my ($chr,$start,$end)=split(/\t/,$line);
	my $additional = $lines->[$idx];
	print OUT "$chr:$start-$end\t$additional\n";
	$idx++;
}
close(IN);
close(OUT);
