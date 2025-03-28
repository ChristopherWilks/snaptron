#!/usr/bin/env perl
use strict;

my $sraprefix="https://trace.ncbi.nlm.nih.gov/Traces/?view=study&acc=";
my %LINKS=('srav3h'=>$sraprefix,'srav1m'=>$sraprefix,'gtexv2'=>'','tcgav2'=>'');

my $compilation=shift;
my $coords=shift;
my $jid=shift;

my $study_link = $LINKS{$compilation};
#print "<html><head>Exon-exon splice-junction ID: $jid</head><body style='font-family: monospace; font-size: 25px;'>\n";
print "<html><head>Exon-exon splice-junction ID: $jid</head><body style='font-family: monospace;'>\n";
my $i=0;
#expect a list of lines, with the first being the jxn coordinates, strand, total_sample_count, and total_coverage_sum
#and the following lines to be <studyID>:<sample_count%>:<coverage_sum%>
while(my $line=<STDIN>) {
    chomp($line);
    $i++;
    print "<p>";
    if($i == 1) {
        
        #($c,$s,$e,$o,$nsamples,$tcov)=split(/\t/,$line,-1);
        #my ($coords,$nsamples,$tcov)=split(/\t/,$line,-1);
        my ($jid0,$c,$s,$e,$o,$nsamples,$tcov,$study) = split(/\t/,$line,-1);
        #print "Exon-exon splice-junction ID: $jid\n";
        #print "<br>Coordinates: $c:$s-$e:$o\n";
        #print "<br>Coordinates: $coords\n";
        print "Coordinates (GRCh38/hg38 for human, GRCm38/mm10 for mouse): $coords:$o\n";
        print "<br><br>Total count of sequence runs (~samples) w/ >= 1 split-read supporting this jxn: $nsamples\n";
        print "<br>Total split-read coverage summed across all samples: $tcov\n";
        print "<br><br>This junction appears in the following studies/tissues/cancers/regions/celltypes, ordered by % of total samples, descending*:\n<br><br>";
        #first study is on this initial line
        $line=$study;
    }
    my ($study,$samplePCT,$covPCT)=split(/:/,$line,-1);
    #print "$study_link"."$study".": sample count %=$samplePCT".", coverage sum %=$covPCT";
    print "$study_link"."$study".": $samplePCT"."% of sample count".", $covPCT"."% of coverage sum";
}
print "</p><br><p style='font-family: monospace;'>*NOTE: sample count and coverage sum %'s are truncated to integers and any 0% studies/tissues are dropped, which is why this list might not sum to 100%\n";
#print"</p><br><p style='font-family: monospace; font-size: 22px;'>Questions about the recount3 data, Monorail pipeline, or Snaptron web services should be posted to: https://github.com/langmead-lab/monorail-external/issues\n";
print "</p><br><p style='font-family: monospace;'>Questions about the recount3 data, Monorail pipeline, or Snaptron web services should be posted to: https://github.com/langmead-lab/monorail-external/issues\n";
print "</p><p style='font-family: monospace;'>If you find this information useful for a publication, please cite:<br><br>\n";
print "Wilks C, Zheng SC, Chen FY, Charles R, Solomon B, Ling JP, Imada EL, Zhang D, Joseph L, Leek JT et al.\n<br>recount3: summaries and queries for large-scale RNA-seq expression and splicing.\n<br>Genome Biol. 2021 Nov 29;22(1):323. PMID: 34844637; PMC: PMC8628444\n";
print "</body></html>\n\r";
