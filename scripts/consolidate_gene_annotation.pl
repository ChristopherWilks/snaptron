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
  #my $fh = \*STDIN;
  my $fh;
  #open($fh,"<$inputF") if($inputF);
  open($fh,"<",$inputF);

  my $cur_transcript_id;
  my $pline="";
  my $pline2="";
  my $tend = -1;
  my $cds_start = -1;
  my $cds_end = -1;
  my $exons = "";
  while(my $line = <$fh>)
  {
    chomp($line);
    next if($line =~/^#/);
    my ($ref,$source,$type,$start,$end,$score,$strand,$frame,$attr) = split(/\t/,$line);
    next if($type !~ /(exon)|(CDS)/);
    my $transcript_id = parse_transcript_id($attr);
    if($cur_transcript_id && $transcript_id ne $cur_transcript_id)
    {
      $exons =~s/,$//;
      my $cds_span = ($cds_start != -1?"$cds_start-$cds_end":"NA");
      print "$pline\t$tend\t$pline2\ttranscript_id \"$cur_transcript_id\";cds_span \"$cds_span\";exons \"$exons\";\n";
      $tend = -1;
      $cds_start = -1;
      $cds_end = -1;
      $exons = "";
      $cur_transcript_id=undef;
    }
    if(!$cur_transcript_id)
    {
      $pline = "$ref\t$SOURCE\ttranscript\t$start";
      $pline2 = ".\t$strand\t.";
    } 
    if($type =~ /exon/i)
    {
      $exons.="$start-$end,";
      $tend = $end;
    }
    if($type =~ /CDS/i)
    {
      $cds_start = $start if($cds_start == -1);
      $cds_end = $end;
    } 
    $cur_transcript_id = $transcript_id;
  }
  if($cur_transcript_id)
  {
    $exons =~s/,$//;
    my $cds_span = ($cds_start != -1?"$cds_start-$cds_end":"NA");
    print "$pline\t$tend\t$pline2\ttranscript_id \"$cur_transcript_id\";cds_span \"$cds_span\";exons \"$exons\";\n";
  }
}  

sub parse_transcript_id
{
  my $attr = shift;
  $attr =~ /transcript_id "([^"]+)";/;
  return $1;
}  
