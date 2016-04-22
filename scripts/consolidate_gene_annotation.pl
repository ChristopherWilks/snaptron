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

my %fname2source=('refGene.gtf'=>'REFGENE','Homo_sapiens.GRCh37.75.gtf'=>'ENSEMBL','gencode.v19.annotation.gtf'=>'GENCODE');

my %sources=('ENSEMBL'=>'ES','REFGENE'=>'RG','GENCODE'=>'GC');

my $inputF = shift;

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
    $source = $sources{$source};
    #print STDERR "$line\n";
    next if($type !~ /(exon)|(CDS)/i);
    if(defined($cur_ref) && $ref ne $cur_ref)
    {
      print_transcript_lines($cur_ref,\%refH);
      %refH=();
    }
    $cur_ref = $ref;
    my $transcript_id = parse_transcript_id($attr);
    if(!defined($refH{$transcript_id}))
    {
      $refH{$transcript_id} = ["","","",-1,-1,-1,""];
      $refH{$transcript_id}->[0] = "transcript\t$start";
      $refH{$transcript_id}->[1] = ".\t$strand\t.";
      $refH{$transcript_id}->[6] = $source;
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
      print_transcript_lines($cur_ref,\%refH);
      %refH=();
  }
}  

sub print_transcript_lines
{
      my $ref = shift;
      my $refH_ = shift;
  
      my %refH = %$refH_;
      #first create collapsed mixed-source transcripsts where necessary
      my %final;
      foreach my $tid (keys %refH)
      {
        my $pline = $refH{$tid}->[0];
        my $pline2 = $refH{$tid}->[1];
        my $exons = $refH{$tid}->[2]; 
        $exons =~s/,$//;
        my $tend = $refH{$tid}->[3]; 
        my $cds_start = $refH{$tid}->[4]; 
        my $cds_end = $refH{$tid}->[5]; 
        my $source = $refH{$tid}->[6];

        my $cds_span = ($cds_start != -1?"$cds_start-$cds_end":"NA");
        #print "$pline\t$tend\t$pline2\ttranscript_id \"$tid\";cds_span \"$cds_span\";exons \"$exons\";\n";
        if($final{$cds_span.":".$exons})
        {
          push(@{$final{$cds_span.":".$exons}->[2]},$source);
          push(@{$final{$cds_span.":".$exons}->[3]},$tid);
        }
        else
        {
          $final{$cds_span.":".$exons}=["$pline\t$tend\t$pline2","cds_span \"$cds_span\";exons \"$exons\";",[$source],[$tid]];
        }
      }

      #now print out
      foreach my $span (keys %final)
      {
        my ($line1,$line2,$source,$tids) = @{$final{$span}};
        my $tids_=join(",",@$tids);
        my $sources = join(",",@$source);
        print "$ref\t$sources\t$line1\ttranscript_id \"$tids_\";$line2\n"; 
        
      }
}

sub parse_transcript_id
{
  my $attr = shift;
  $attr =~ /transcript_id "([^"]+)";/;
  return $1;
}  
