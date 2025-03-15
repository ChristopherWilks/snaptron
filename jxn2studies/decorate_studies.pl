#!/usr/bin/env perl
use strict;

my $sraprefix="https://trace.ncbi.nlm.nih.gov/Traces/?view=study&acc=";
my %LINKS=('srav3h'=>$sraprefix,'srav1m'=>$sraprefix,'gtexv2'=>'','tcgav2'=>'');

my $compilation=shift;
my $jid=shift;

my $study_link = $LINKS{$compilation};
print "<html><head>Exon-exon splice-junction ID: $jid</head><body style='font-family: monospace; font-size: 25px;'>\n";
my $i=0;
#expect a list of lines, with the first being the jxn coordinates, strand, total_sample_count, and total_coverage_sum
#and the following lines to be <studyID>:<sample_count%>:<coverage_sum%>
while(my $line=<STDIN>) {
    chomp($line);
    $i++;
    print "<p>";
    if($i == 1) {
        #($c,$s,$e,$o,$nsamples,$tcov)=split(/\t/,$line,-1);
        my ($coords,$nsamples,$tcov)=split(/\t/,$line,-1);
        #print "Exon-exon splice-junction ID: $jid\n";
        #print "<br>Coordinates: $c:$s-$e:$o\n";
        #print "<br>Coordinates: $coords\n";
        print "Coordinates (GRCh38/hg38 for human, GRCm38/mm10 for mouse): $coords\n";
        print "<br><br>Total count of sequence runs (~samples) w/ >= 1 split-read supporting this jxn: $nsamples\n";
        print "<br>Total split-read coverage summed across all samples: $tcov\n";
        print "<br>This junction appears in the following studies/tissues, ordered by % of total samples, descending:\n";
        next;
    } else { 
        my ($study,$samplePCT,$covPCT)=split(/:/,$line,-1);
        print "$study_link"."$study".": sample count %=$samplePCT".", coverage sum %=$covPCT";
    }
    print "</p><br><br><p style='font-family: monospace; font-size: 20px;'>If you find this information useful for a publication, please cite:<br><br>\n";
    print "Wilks C, Zheng SC, Chen FY, Charles R, Solomon B, Ling JP, Imada EL, Zhang D, Joseph L, Leek JT et al.\n<br>recount3: summaries and queries for large-scale RNA-seq expression and splicing.\n<br>Genome Biol. 2021 Nov 29;22(1):323. PMID: 34844637; PMC: PMC8628444\n";
}
print "</body></html>\n\r";
