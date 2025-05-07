#!/usr/bin/env perl
use strict;

my $sraprefix="https://trace.ncbi.nlm.nih.gov/Traces/?view=study&acc=";
my %LINKS=('srav3h'=>$sraprefix,'srav1m'=>$sraprefix,'gtexv2'=>'','tcgav2'=>'');

my $compilation=shift;
my $coords=shift;
my $jid=shift;

#jxn_details.template.html
#my $templateF=shift;
my $templateF="/srv/nvme1/snaptron/jxn2studies/jxn_details.template.html";

open(IN,"<$templateF");
my @template=<IN>;
close(IN);
my $template=join("\n",@template);
#print "$template\n";
#exit(0);

my $study_link = $LINKS{$compilation};
$template=~s/REPLACE:ID/$jid/g;
$template=~s/REPLACE:COMPILATION/$compilation/g;
my $rows="";
my $i=0;
#expect a list of lines, with the first being the jxn coordinates, strand, total_sample_count, and total_coverage_sum
#and the following lines to be <studyID>:<sample_count%>:<coverage_sum%>
while(my $line=<STDIN>) {
    chomp($line);
    $i++;
    print "<p>";
    if($i == 1) {
        
        my ($jid0,$c,$s,$e,$o,$nsamples,$tcov,$study) = split(/\t/,$line,-1);
        $template=~s/REPLACE:RECOUNT_ID/$coords:$o/g;
        $template=~s/REPLACE:COUNT/$nsamples/g;
        $template=~s/REPLACE:COVERAGE/$tcov/g;
        #first study is on this initial line
        $line=$study;
    }
    my ($study,$samplePCT,$covPCT)=split(/:/,$line,-1);
    if(length($study_link) > 0) {
        $rows.='<tr><td><a href="'."$study_link"."$study".'" target="_blank">'."$study"."</a></td><td>".$samplePCT."%</td><td>".$covPCT."%</td></tr>\n";
    } else {
        $rows.="<tr><td>"."$study"."</td><td>".$samplePCT."%</td><td>".$covPCT."%</td></tr>\n";
    }
}
$template=~s/REPLACE:ROWS/$rows/;
print "$template\n\r";
