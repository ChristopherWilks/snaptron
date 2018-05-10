#!/bin/bash
#$1 is the path to the rail top level directry of the rail results, e.g. /work-zfs/blangme2/langmead/rail-runs/celltower
#$2 is the file/directry naming convention for the rail manifest files (to get the # of samples), e.g. "ct_mouse_sc_part"
#$3 is number of parallel sort jobs to run
#$4 generic filename of the junctions file from each rail output (either "first_pass_junctions.tsv.gz" or "junctions.tsv.gz")

#do first pass junctions
find -L ${1} -name "${4}" | perl -ne 'chomp; $f=$_; next if($f!~/'${2}'/); @f=split(/\//,$f); $f=~/part(\d\d)/; $n=$1; `ln -fs $f $n.tsv.gz`;'

#get list of sample SRP-SRRs with file ID
ls ${1}/${2}*/${2}*.manifest | perl -ne 'chomp; $f=$_; $f=~/part(\d\d)\.manifest/; $n=$1; open(IN,"<$f"); $c=0; for $i (<IN>) { print "$n\t".($c++)."\t$i"; }' | cut -f1,2,5 > all_samples.tsv

#requires GNU parallel
#number of samples per file
#module load parallel
#choose the largest number of samples in any given split sample group
NUM_SAMPLES=`wc -l ${1}/${2}*/${2}*.manifest | grep "${2}" | perl -ne '@f=split(/\s+/,$_); print "".$f[1]."\n";' | sort -n | tail -n1`
NUM_PARALLEL=${3}
TDIR=/home-1/cwilks3@jhu.edu/storage/cwilks/tmp

#need to sort all inputs of subsets of junctions so we can merge on coordinate
ls *.gz | perl -ne 'chomp; $f=$_; print "zcat $f | sort -s -t\"	\" -k1,1 -k3,3n -k4,4n > $f.sorted\n";' > sort.jobs
parallel -j${NUM_PARALLEL} < sort.jobs > sort.jobs.run
ls *.sorted | perl -ne 'chomp; $f=$_; $f=~/^(\d\d)/; $fn=$1; $i=0; for $n (`cat $f`) { chomp($n); @f=split(/\t/,$n); print "$fn.$i\t".$f[0]."\t".$f[2]."\t".$f[3]."\n"; $i++;}' | sort -s -t'	' -k2,2 -k3,3n -k4,4n -k1,1 > all_file_coords_sorted.tsv

#now we do the actual merge
python merge_sorted_rail_junctions.py $NUM_SAMPLES all_file_coords_sorted.tsv all_samples.tsv `ls ??.tsv.gz.sorted` 2> samples_map.tsv | sort -T $TDIR -t'	' -k1,1 -k2,2n -k3,3n | tee > merged.junctions.tsv | gzip > merged.junctions.tsv.gzip

#will need the rail_id2SRR accession map later when creating the Snaptron compilation
cut -f 2,3 samples_map.tsv | sort -t'	' -k1,1n > samples_map.sorted.tsv
#creates the header for the base coverage Snaptron response based on the newly created rail_ids
cut -f 1 samples_map.sorted.tsv | perl -ne 'BEGIN { print "chromosome\tstart\tend"; } chomp; print "\t$_"; END { print "\n";}' > samples_map.sorted.tsv.single_line

###Tests
#check for out-of-order junction
cut -f 1,3,4 merged.junctions.tsv | perl -ne 'chomp; $i++; $n=$_; ($c,$s,$e)=split(/\t/,$n); if($pc && $pc eq $c && $s < $ps) { print "$i\t$pc\t$ps\t$pe\t$c\t$s\t$e\n"; } $pc=$c; $ps=$s; $pe=$e;' > out_of_order.bad
#check for emtpy sample IDs
cut -f 5 merged.junctions.tsv | perl -ne 'chomp; $f=$_; $i++; if($f=~/,,/ || $f=~/\t,/ || $f=~/,$/) { print "$i\t$f\n"; }' > empty_sample_ids.bad
#check the number of unique sample_ids in every junction's list and compare with the sample_map
cut -f 5 merged.junctions.tsv | perl -ne 'chomp; for $i (split(/,/,$_)) { $h{$i}=1; } END { for $i (keys %h) { print "$i\n"; }' | sort -n > merged.junctions.tsv.num_samples_total &
cut -f 1 samples_map.sorted.tsv > samples_map.sorted.tsv.rail_ids
diff samples_map.sorted.tsv.rail_ids merged.junctions.tsv.num_samples_total
ls *.bad
