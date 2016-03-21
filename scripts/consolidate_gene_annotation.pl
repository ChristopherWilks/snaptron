#!/usr/bin/perl
use strict;
use warnings;

#takes a gene annotation GTF file and produces a
#coalesced gene annotation GTF where transcripts
#are self contained on their own line with exons 
#all listed in the "attribute" field and the cds_span is defined
#in attribute as well

#expects sorted-by-start-coordinate-within-refs as input
#e.g. sort -t'\t' -s -k1,1 -k4,4n -k5,5n refGene.gtf > refGene.gtf.sorted

#grouping for a transcript is done on the transcript_id
#but since exons/cds features can span multiple transcripts *when sorted on coordinate*
#use a hash per transcript_id and then only print out the final set of full transcripts
#when the current chromsome (ref) is finished, this balances memory use vs. picking up
#straggling features

my %fname2source=('refGene.gtf'=>'REFGENE','Homo_sapiens.GRCh37.75.gtf'=>'ENSEMBLE','gencode.v19.annotation.gtf'=>'GENCODE');

my $inputF = shift;
my $SOURCE = shift;

if(!$SOURCE)
{
  my @f_ = split(/\//,$inputF);
  $SOURCE = pop(@f_);
  $SOURCE = $fname2source{$SOURCE};
  $SOURCE = 'UNKNOWN' if(!$SOURCE || length($SOURCE) == 0);
}

main();

sub main
{
  my $fh;
  open($fh,"<",$inputF);

  my $pline="";
  my $pline2="";
  my $tend = -1;
  my $cds_start = -1;
  my $cds_end = -1;
  my $exons = "";
  my %refH;
  my $cur_ref;
  while(my $line = <$fh>)
  {
    chomp($line);
    next if($line =~/^#/);
    my ($ref,$source,$type,$start,$end,$score,$strand,$frame,$attr) = split(/\t/,$line);
    next if($type !~ /(exon)|(CDS)/i);
    if(defined($cur_ref) && $ref ne $cur_ref)
    {
      print_transcript_lines(\%refH);
      %refH=();
    }
    $cur_ref = $ref;
    my $transcript_id = parse_transcript_id($attr);
    if(!defined($refH{$transcript_id}))
    {
      $refH{$transcript_id} = ["","","",-1,-1,-1];
      $refH{$transcript_id}->[0] = "$ref\t$SOURCE\ttranscript\t$start";
      $refH{$transcript_id}->[1] = ".\t$strand\t.";
    }
    if($type =~ /exon/i)
    {
      $refH{$transcript_id}->[2].="$start-$end,";
      $refH{$transcript_id}->[3] = $end;
    }
    if($type =~ /CDS/i)
    {
      $refH{$transcript_id}->[4] = $start if($refH{$transcript_id}->[4] == -1);
      $refH{$transcript_id}->[5] = $end;
    } 
  }
  if(defined($cur_ref))
  {
      print_transcript_lines(\%refH);
      %refH=();
  }
}  

sub print_transcript_lines
{
      my $refH_ = shift;
  
      my %refH = %$refH_;
      foreach my $tid (keys %refH)
      {
        my $pline = $refH{$tid}->[0];
        my $pline2 = $refH{$tid}->[1];
        my $exons = $refH{$tid}->[2]; 
        $exons =~s/,$//;
        my $tend = $refH{$tid}->[3]; 
        my $cds_start = $refH{$tid}->[4]; 
        my $cds_end = $refH{$tid}->[5]; 
        my $cds_span = ($cds_start != -1?"$cds_start-$cds_end":"NA");
        print "$pline\t$tend\t$pline2\ttranscript_id \"$tid\";cds_span \"$cds_span\";exons \"$exons\";\n";
      }
}

sub parse_transcript_id
{
  my $attr = shift;
  $attr =~ /transcript_id "([^"]+)";/;
  return $1;
}  
