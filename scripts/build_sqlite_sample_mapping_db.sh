#!/bin/bash

#create the sqlite3 table
sqlite3 ${1}.sqlite "CREATE TABLE by_sample_id (sample_id INTEGER NOT NULL,snaptron_ids TEXT NOT NULL,PRIMARY KEY (sample_id));"

#create the sample2junction ID mapping and populate the sqlite3 table
mkfifo ./import
zcat ${2} | cut -f1,12 | perl -ne 'chomp; ($tid,$sid)=split(/\t/,$_); @sids=split(/,/,$sid); foreach $s (@sids) { print "$s\t$tid\n";}' | sort -k1,1 -n | perl -ne 'chomp; $s=$_; ($sid,$tid)=split(/\t/,$s); if(defined($pid) && $pid != $sid) { print "$pid\t"; foreach $s (sort keys %h) {print "$s,";} print "\n"; %h=();} $pid=$sid; $h{$tid}=1; END { if(defined($pid)) { print "$pid\t"; foreach $s (sort keys %h) {print "$s,";} print "\n";}}' > ./import &
sqlite3 ${1}.sqlite -cmd '.separator "\t"' ".import ./import by_sample_id"
rm ./import
