#!/usr/bin/perl
use strict;
use warnings;

#redo what find_gene-rp_overlaps.py does but using perl and tabix, this is for sanity checking

my $intronsF = shift;
my $repeatsF = shift;
my $genesF = shift;

#loop through genes
    #tabix repeats from transcript coords        
    #loop through the exons for each gene
        #tabix introns for list of introns
            #record left or right coord of intron which overlaps exon
            #loop through repeas, record where current intron overlaps repeat and what coord
            #print full intron line with repeat and which end overlaps exon

#external, run a 2nd script to post-process output, any intron with both ends in an exon, filter out

main();

sub main
{
	process_genes($genesF);
}

sub process_genes
{
	my $file = shift;
	open(IN,"<$file");
     	<IN>;
	my %iseen;
	while(my $line = <IN>)
	{
		chomp($line);
		my @f = split(/\t/,$line);
		my $chr = $f[2];
		my $strand = $f[3];
		my ($cluster_id,$gname,$start,$end) = ($f[0],$f[12],$f[4],$f[5]);
		#adjust for UCSC 0-based start
		$start+=1;
		my $repeatsA = get_overlaps_via_tabix($chr,$start,$end,$repeatsF);
		my @estarts = split(/,/,$f[9]);		
		my @eends = split(/,/,$f[10]);
		for(my $i=0;$i<scalar @estarts;$i++)
		{
			my ($estart,$eend) = ($estarts[$i],$eends[$i]);
			#adjust for UCSC 0-based start
			$estart+=1;
			my $intronsA = get_overlaps_via_tabix($chr,$estart,$eend,$intronsF);
			foreach my $intron (@$intronsA)
			{
				chomp($intron);
				my @ifields = split(/\t/,$intron);
				my ($iid,$ichr,$istart,$iend) = ($ifields[0],$ifields[1],$ifields[2],$ifields[3]);
				#make sure the intron IS fully within the transcript
				next if($istart < $start || $iend > $end);
				#make sure intron IS NOT fully contained within exon
				next if($istart >= $estart && $iend <= $eend);
				my $coord_in_exon = $istart;
				$coord_in_exon = $iend if($iend >= $estart && $iend <= $eend);
				#check to see if this intron's other end is already in an exon
				#next if($iseen{$iid} && $iseen{$iid} != $coord_in_exon);
				$iseen{$iid}->{$coord_in_exon}=1;
				intersect_introns_and_repeats(\@ifields,$repeatsA,$coord_in_exon,$cluster_id,$gname,$strand,$start,$end);
			}
		}
	}
	close(IN);
	#now determine which introns need to be removed
	foreach my $iid (keys %iseen)
	{
		if(scalar keys %{$iseen{$iid}} < 2)
		{
			print "$iid\n";
		}
	}	
}




sub intersect_introns_and_repeats
{
	my $ifields_ = shift;
	my $repeatsA = shift;
	my $coord_in_exon = shift;
	my $cluster_id = shift;
	my $gname = shift;
	my $gstrand = shift;
	my $gstart = shift;
	my $gend = shift;

	my @ifields = @$ifields_;
	my $intron_line = join("\t",@ifields);
	my ($ichr,$istart,$iend) = ($ifields[1],$ifields[2],$ifields[3]);
	my $coord_in_repeat = $istart;
	$coord_in_repeat = $iend if($istart == $coord_in_exon);
	
	foreach my $repeat (@$repeatsA)
	{
		chomp($repeat);
		my @rfields = split(/\t/,$repeat);
		my ($rchr,$rstart,$rend,$rstrand,$rname,$rtype) = ($rfields[5],$rfields[6],$rfields[7],$rfields[9],$rfields[10],$rfields[11]);
		if($rchr ne $ichr)
		{
			die "repeat chr != intron chr, should never get here! $rchr $ichr\n";
		}
		#assume repeat coords are already 1-based
		#intron coord must be overlapping repeat
		next if($coord_in_repeat < $rstart || $coord_in_repeat > $rend);
		print "$cluster_id\t$gname\t$gstrand\t$gstart\t$gend\t$rstart\t$rend\t$rstrand\t$rname\t$rtype\t$coord_in_exon\t$intron_line\n";
	}
}

sub get_overlaps_via_tabix
{
	my $chr=shift;
	my $start=shift;
	my $end=shift;
	my $OVERLAP_FILE=shift;

	my @overlaps = `tabix $OVERLAP_FILE $chr:$start-$end`;
	if(!@overlaps || scalar @overlaps == 0)
	{
		#print STDERR "Either error in tabix or no overlaps in $OVERLAP_FILE for $chr:$start-$end\n";
		return [];
	}
	return \@overlaps;
}	
