#!/bin/bash

sqlite3 ${1}.sqlite "CREATE TABLE intron (snaptron_id int(11) NOT NULL,chrom varchar(20) DEFAULT NULL,start int(11) DEFAULT NULL,end int(11) DEFAULT NULL,length int(11) DEFAULT NULL,strand char(1) NOT NULL,annotated tinyint(1) DEFAULT 0,donor char(2) DEFAULT NULL,acceptor char(2) DEFAULT NULL,left_annotated LONGTEXT DEFAULT "0",right_annotated LONGTEXT DEFAULT "0",samples LONGTEXT DEFAULT NULL,samples_count int(11) DEFAULT 0,coverage_sum int(11) DEFAULT 0,coverage_avg float(11) DEFAULT 0.0,coverage_median float(11) DEFAULT 0.0,source_dataset_id int(3) DEFAULT NULL,PRIMARY KEY(snaptron_id));"

mkfifo ./import
zcat $2 > ./import  &
sqlite3 ${1}.sqlite -cmd '.separator "\t"' ".import ./import intron"

sqlite3 ${1}.sqlite "CREATE INDEX chrom_start_end_idx ON intron(chrom,start,end);"
rm ./import
