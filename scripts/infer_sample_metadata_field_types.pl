#!/usr/bin/perl
use strict;
use warnings;

my $n=0;
my %counts;
while(my $line = <STDIN>)
{
	chomp($line); 
	$n++; 
	my @f=split(/\t/,$line); 
	foreach my $idx (0 .. (scalar @f)-1) 
	{ 
		#default type is Text
		my $type="t"; 
		#NAs or empty/space strings are flagged as "N"
		$type="n" if($f[$idx] eq "NA" || $f[$idx] =~ /^\s*$/); 
		$type="f" if($f[$idx]=~/^-?\d+?\.?\d+$/ || $f[$idx] =~ /e\+/);
		$type="i" if($f[$idx]=~/^-?\d+$/); 
		$counts{$idx}->{$type}++; 
	} 
}
	
foreach my $idx (sort { $a<=>$b} keys %counts) 
{ 
	print "$idx"; 
	$counts{$idx}->{"n"}=-$counts{$idx}->{"n"} if(defined($counts{$idx}->{"n"})); 
	$counts{$idx}->{"i"}=-$counts{$idx}->{"i"} if(defined($counts{$idx}->{"f"}) && defined($counts{$idx}->{"i"}) > 0); 
	foreach my $t (sort {$counts{$idx}->{$b}<=>$counts{$idx}->{$a}} keys %{$counts{$idx}}) 
	{ 
		print "\t$t,".$counts{$idx}->{$t}; 
	} 
	print "\n";
}

