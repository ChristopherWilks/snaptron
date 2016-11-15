#!/bin/bash

sqlite3 ${1}.sqlite "CREATE TABLE intron (snaptron_id int(11) NOT NULL,chrom varchar(20) DEFAULT NULL,start int(11) DEFAULT NULL,end int(11) DEFAULT NULL,length int(11) DEFAULT NULL,strand char(1) NOT NULL,annotated tinyint(1) DEFAULT 0,donor char(2) DEFAULT NULL,acceptor char(2) DEFAULT NULL,left_annotated LONGTEXT DEFAULT "0",right_annotated LONGTEXT DEFAULT "0",samples LONGTEXT DEFAULT NULL,read_coverage_by_sample LONGTEXT DEFAULT NULL,samples_count int(11) DEFAULT 0,coverage_sum int(11) DEFAULT 0,coverage_avg float(11) DEFAULT 0.0,coverage_median float(11) DEFAULT 0.0,source_dataset_id int(3) DEFAULT NULL,PRIMARY KEY(snaptron_id));"

zcat $2 > /data/import &
sqlite3 ${1}.sqlite -cmd '.separator "\t"' ".import /data/import intron"

sqlite3 ${1}.sqlite "CREATE INDEX samples_count_idx ON intron (samples_count); CREATE INDEX coverage_sum_idx ON intron (coverage_sum); CREATE INDEX coverage_avg_idx ON intron (coverage_avg); CREATE INDEX chrom_start_end_idx ON intron(chrom,start,end); CREATE INDEX length_idx ON intron (length);"
