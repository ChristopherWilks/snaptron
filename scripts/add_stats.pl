#!/usr/bin/perl
use strict;
use warnings;

#ID each SRP, count coverage for each SRP, divide sum of coverage for each SRP by total count of samples in that SRP (precomute this last bit)
#call original average and media something else (TF-IDF)

my $id_mappingF=shift;

#my $smd = load_sample_metadata($smdf);
my ($ids,$studies,$samples) = load_id_mapping($id_mappingF);

while(my $line = <STDIN>)
{
    chomp($line);
    my @f = split(/\t/,$line);
    my @s = split(/,/,$f[12]); 
    my @r = split(/,/,$f[13]);
    my %study;
    my %sample;
    foreach my $idx (0 .. (scalar @s)-1)
    {
      my $s = $s[$idx];
      my $r = $r[$idx];
      #my $srp = $smd->{$s}->[1];
      #my $srs = $smd->{$s}->[2];
      my ($srs,$srp) = @{$ids->{$s}};
      $study{$srp}+=$r;
      $sample{$srs}+=$r;
    }
    my $srps = "";
    my $srps_ids = "";
    foreach my $srp (sort {$a cmp $b} keys %study)
    {
      my $size = $studies->{$srp}; 
      my $count = $study{$srp};
      $srps_ids .= "$srp,";
      $srps .= sprintf("%.3f,",$count/$size);
    }
    my $srss = "";
    my $srss_ids = "";
    foreach my $srp (sort {$a cmp $b} keys %sample)
    {
      my $size = $samples->{$srp}; 
      my $count = $sample{$srp};
      $srss_ids .= "$srp,";
      $srss .= sprintf("%.3f,",$count/$size);
    }
    $srps_ids=~s/,$//;
    $srps=~s/,$//;
    $srss=~s/,$//;
    $srss_ids=~s/,$//;
    print "$line\t$srss_ids\t$srss\t$srps_ids\t$srps\n"; 
}
    
sub load_id_mapping
{
    my $file = shift;

    my %ids;
    my %srps;
    my %srss;
    open(IN,"<$file");
    while(my $line = <IN>)
    {
      chomp($line);
      my ($id,$srs_sz,$srp_sz,$srp,$srp_id,$srs,$srs_id)=split(/\t/,$line);
      $ids{$id}=[$srs_id,$srp_id];
      $srss{$srs_id}=$srs_sz;
      $srps{$srp_id}=$srp_sz;
    }
    close(IN);
    return (\%ids,\%srps,\%srss);
}
