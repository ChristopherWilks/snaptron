all: jx_stats process_exon_coverage

process_exon_coverage: process_exon_gene_sums_into_snaptron_format.cpp
	g++ -O3 -std=c++11 process_exon_gene_sums_into_snaptron_format.cpp -o process_exon_coverage

jx_stats: compute_jx_stats_for_snaptron_format.cpp
	g++ -O3 -std=c++11 compute_jx_stats_for_snaptron_format.cpp -o jx_stats

debug: compute_jx_stats_for_snaptron_format.cpp
	g++ -g -std=c++11 compute_jx_stats_for_snaptron_format.cpp -o jx_stats-debug

clean: 
	rm jx_stats jx_stats-debug
