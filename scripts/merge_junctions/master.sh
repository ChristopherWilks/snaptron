#!/bin/bash
#requires GNU parallel
#number of samples per file
NUM_SAMPLES=1320

ls *.gz | perl -ne 'chomp; $f=$_; print "zcat $f | sort -s -t\"	\" -k1,1 -k3,3n -k4,4n > $f.sorted\n";' > sort.jobs
parallel -j12 < sort.jobs
ls *.sorted | perl -ne 'chomp; $f=$_; $f=~/^(\d\d)/; $fn=$1; $i=0; for $n (`cat $f`) { chomp($n); @f=split(/\t/,$n); print "$fn.$i\t".$f[0]."\t".$f[2]."\t".$f[3]."\n"; $i++;}' | sort -s -t'	' -k2,2 -k3,3n -k4,4n -k1,1 > all_file_coords_sorted.tsv
python merge_sorted_rail_junctions.py $NUM_SAMPLES all_file_coords_sorted.tsv 01.tsv.gz.sorted 02.tsv.gz.sorted 03.tsv.gz.sorted 04.tsv.gz.sorted 05.tsv.gz.sorted 06.tsv.gz.sorted 07.tsv.gz.sorted 08.tsv.gz.sorted 09.tsv.gz.sorted 10.tsv.gz.sorted 13.tsv.gz.sorted 14.tsv.gz.sorted > merged.junctions.tsv 2>errs

###Tests
#do a spot check
fgrep 'chr1	+	9865349	9868382' merged.junctions.tsv > result.1
diff test.1 result.1
#check for out-of-order junction
cut -f 1,3,4 merged.junctions.tsv | perl -ne 'chomp; $i++; $n=$_; ($c,$s,$e)=split(/\t/,$n); if($pc && $pc eq $c && $s < $ps) { print "$i\t$pc\t$ps\t$pe\t$c\t$s\t$e\n"; } $pc=$c; $ps=$s; $pe=$e;' > bad
head bad
