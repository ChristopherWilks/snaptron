create table intron2 (gigatron_id int(11) NOT NULL,
                      chromosome varchar(20) DEFAULT NULL,
                      start int(11) DEFAULT NULL,
                      end int(11) DEFAULT NULL,
                      start_end LINESTRING NOT NULL,
                      strand char(1) NOT NULL,
                      donor char(2) DEFAULT NULL,
                      acceptor char(2) DEFAULT NULL,
                      samples LONGTEXT DEFAULT NULL,
                      read_coverage_by_sample LONGTEXT DEFAULT NULL,
                      samples_count int(11) DEFAULT 0,
                      coverages_count int(11) DEFAULT 0,
                      coverage_sum int(11) DEFAULT 0,
                      coverage_avg float(11) DEFAULT 0.0,
                      coverage_median float(11) DEFAULT 0.0,
                      PRIMARY KEY(gigatron_id),
                      index start_idx USING BTREE (start),
                      index end_idx USING BTREE (end),
                      index samples_count_idx USING BTREE (samples_count),
                      index coverage_sum_idx USING BTREE (coverage_sum),
                      index coverage_avg_idx USING BTREE (coverage_avg),
                      index coverage_median_idx USING BTREE (coverage_median), 
                      spatial index(start_end)
                      ) ENGINE=MyISAM DEFAULT CHARSET=utf8;

SET foreign_key_checks = 0;
LOAD DATA INFILE '/data2/gigatron2/all_SRA_introns_ids_stats.tsv.gz.1000.no_double_counts' INTO TABLE intron (gigatron_id,chromosome,@start,@end,strand,donor,acceptor,samples,read_coverage_by_sample,samples_count,coverage_sum,coverage_avg,coverage_median) SET start_end = LineFromText('LINESTRING(@start @start,@end @end)');

#this works
LOAD DATA INFILE '/data2/gigatron2/all_SRA_introns_ids_stats.tsv.new.wo_header' INTO TABLE intron2 (gigatron_id,chromosome,start,end,strand,donor,acceptor,samples,read_coverage_by_sample,samples_count,coverages_count,coverage_sum,coverage_avg,coverage_median) set start_end=LineFromText(CONCAT('LINESTRING(',start,' ',start,',',end,' ',end,')'));

