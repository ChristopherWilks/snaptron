#!/bin/bash
#$1 is the path to the rail top level directry of the rail results, e.g. /work-zfs/blangme2/langmead/rail-runs/celltower
#$2 is the file/directry naming convention for the rail manifest files (to get the # of samples), e.g. "ct_mouse_sc_part"
#$3 is number of parallel sort jobs to run

#do 2nd pass junctions
find -L ${1} -name "junctions.tsv.gz" | perl -ne 'chomp; $f=$_; next if($f!~/'${2}'/); @f=split(/\//,$f); $f=~/part(\d\d)/; $n=$1; `ln -fs $f $n.tsv.gz`;'

#get list of sample SRP-SRRs with file ID
ls ${1}/${2}*/${2}*.manifest | perl -ne 'chomp; $f=$_; $f=~/part(\d\d)\.manifest/; $n=$1; open(IN,"<$f"); $c=0; for $i (<IN>) { print "$n\t".($c++)."\t$i"; }' | cut -f1,2,5 > all_samples.tsv

#requires GNU parallel
#number of samples per file
module load parallel
#choose the largest number of samples in any given split sample group
NUM_SAMPLES=`wc -l ${1}/${2}*/${2}*.manifest | grep "${2}" | perl -ne '@f=split(/\s+/,$_); print "".$f[1]."\n";' | sort -n | tail -n1`
NUM_PARALLEL=${3}
TDIR=/home-1/cwilks3@jhu.edu/storage/cwilks/tmp

ls *.gz | perl -ne 'chomp; $f=$_; print "zcat $f | sort -s -t\"	\" -k1,1 -k3,3n -k4,4n > $f.sorted\n";' > sort.jobs
parallel -j${NUM_PARALLEL} < sort.jobs
ls *.sorted | perl -ne 'chomp; $f=$_; $f=~/^(\d\d)/; $fn=$1; $i=0; for $n (`cat $f`) { chomp($n); @f=split(/\t/,$n); print "$fn.$i\t".$f[0]."\t".$f[2]."\t".$f[3]."\n"; $i++;}' | sort -s -t'	' -k2,2 -k3,3n -k4,4n -k1,1 > all_file_coords_sorted.tsv
python merge_sorted_rail_junctions.py $NUM_SAMPLES all_file_coords_sorted.tsv all_samples.tsv `ls ??.tsv.gz.sorted` | sort -T $TDIR -t'	' -k1,1 -k2,2n -k3,3n > merged.junctions.tsv 2>errs

###Tests
#do a spot check
fgrep 'chr1	+	9865349	9868382' merged.junctions.tsv > result.1
#diff test.1 result.1
#check for out-of-order junction
cut -f 1,3,4 merged.junctions.tsv | perl -ne 'chomp; $i++; $n=$_; ($c,$s,$e)=split(/\t/,$n); if($pc && $pc eq $c && $s < $ps) { print "$i\t$pc\t$ps\t$pe\t$c\t$s\t$e\n"; } $pc=$c; $ps=$s; $pe=$e;' > bad
#head bad
