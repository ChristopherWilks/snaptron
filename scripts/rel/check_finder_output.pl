#!/usr/bin/perl
use strict;
use warnings;

my $file = shift;
open(IN,"<$file");

while(my $line = <IN>)
{
	chomp($line);
	next if($line =~ /^\s*$/);
	my @f = split(/\t/,$line);
	my ($rcoord,$gstrand,$gspans,$rstrand,$rspans,$sense_match,$chr,$st,$en,$strand) = ($f[0],$f[3],$f[4],$f[7],$f[8],$f[9],$f[11],$f[12],$f[13],$f[15]);

	my $gcoord = $st;
	$gcoord = $en if($rcoord == $gcoord);
	my $gbad = check_for_bad_spans($gspans,$gcoord,"gene");
	my $rbad = check_for_bad_spans($rspans,$rcoord,"repeat");
	check_strand($line,$gstrand,$rstrand,$strand,$sense_match);
}
close(IN);

sub check_strand
{
	my $line = shift;
	my $gstrand = shift;
	my $rstrand = shift;
	my $strand = shift;
	my $sense_match = shift;

	my %gstrands;
	my %rstrands;
	map {$gstrands{$_}=1;} split(/;/,$gstrand);
	print "STRAND_ERROR\tgene\t$strand\t$line\n" if(!$gstrands{$strand} && $sense_match eq 'True');
	map {$rstrands{$_}=1;} split(/;/,$rstrand);
	print "STRAND_ERROR\trepeat\t$strand\t$line\n" if(!$rstrands{$strand} && $sense_match eq 'True');
}

sub check_for_bad_spans
{
	my $spans=shift;
	my $coord = shift;
	my $type = shift;

	my @spans = split(/;/,$spans);
	foreach my $span (@spans)
	{
		my ($s,$e)=split(/\-/,$span);
		if($coord < $s || $coord > $e)
		{
			print "SPAN_ERROR\t$type\t$coord\t$span\n";
			return 1;
		}
	}
	return 0;
}
