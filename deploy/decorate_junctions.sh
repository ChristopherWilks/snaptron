#!/bin/bash
#assumes we're in the top level of the clone of Snaptron git repo
#3 arguments required:
#1) gzipped input file of raw tab-delimited junctions format: chr,start,end,strand,left_motif,right_motif,sample_id_list,sample_coverage_list
#2) output name of BGZip file which decorated junctions will be written to for indexing by Tabix
#3) full path to set of human genome reference-specific annotations to use to mark which junctions are known

#decorate the raw junctions with 1) annotations and 2) sample stats
gzip -cd ${1} | pypy ./annotations/process_introns.py --annotations ${3} | perl -ne 'BEGIN {$data_source_id=4;} chomp; $s=$_; @f=split(/\t/,$s); @f1=split(/,/,$f[11]); @f2=split(/,/,$f[12]); $f1=scalar @f1; $f2=scalar @f2; $s2=0; map { $s2+=$_; } @f2; $avg=$s2/$f2; $median=-1; $m_=$f2/2; $m_=int($m_); @f2a=sort {$a<=>$b} @f2; if(($f2 % 2)==0) { $m2_=$f2/2; $m2_-=1; $median=($f2a[$m_]+$f2a[$m2_])/2; } else { $median=$f2a[$m_]; }  printf("$s\t$f1\t$s2\t%.3f\t%.3f\t$data_source_id\n",$avg,$median);' | bgzip > ${2}

#now do sample2junction mapping
zcat ${2} | cut -f1,12 | perl -ne 'chomp; ($tid,$sid)=split(/\t/,$_); @sids=split(/,/,$sid); foreach $s (@sids) { print "$s\t$tid\n";}' | sort -k1,1 -n | perl -ne 'chomp; $s=$_; ($sid,$tid)=split(/\t/,$s); if(defined($pid) && $pid != $sid) { print "$pid\t"; foreach $s (sort keys %h) {print "$s,";} print "\n"; %h=();} $pid=$sid; $h{$tid}=1; END { if(defined($pid)) { print "$pid\t"; foreach $s (sort keys %h) {print "$s,";} print "\n";}}' | bzip2 > ${2}.sample2junction_ids.bz2

#now index
tabix -s 2 -b 3 -e 4 ${2}

#setup the sqlite3 junction database used for joint interval + range (threshold) queries
./scripts/build_sqlite_junction_db.sh ${2} ${2}

#setup the sqlite3 sample_id2junction_id mapping database to allow for filtering junctions by the samples they appear in
./scripts/build_sqlite_sample_mapping_db.sh ${2}.sample2junction_ids ${2}.sample2junction_ids.bz2
