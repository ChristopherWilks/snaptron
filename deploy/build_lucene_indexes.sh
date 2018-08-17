#!/bin/bash
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`
root=$scripts/../
source $root/python/bin/activate

create_all=$1
#build Lucene metadata indices (assumes samples.tsv is present and is sorted by rail_id in ascending order)
#also assumes we're in the directory where all the snaptron compilation data is at
if [[ $create_all == "all" ]]; then
	perl -e 'print "rail_id\tjunction_count\tjunction_coverage\tjunction_avg_coverage\n";' > jx_stats_per_sample.tsv
	zcat junctions.bgz | cut -f 12 | perl -ne 'chomp; @f=split(/,/,$_); shift(@f); for $f (@f) { ($f,$c)=split(/:/,$f); $count{$f}++; $cov{$f}+=$c; } END { for $f (keys %count) { $avg=$cov{$f}/$count{$f}; print "$f\t".$count{$f}."\t".$cov{$f}."\t$avg\n";}}' | sort -t'	' -k1,1n >> jx_stats_per_sample.tsv
	paste samples.tsv <(cut -f 2- jx_stats_per_sample.tsv) > samples.jx.tsv
	mv samples.jx.tsv samples.tsv
fi
cat samples.tsv | perl $scripts/infer_sample_metadata_field_types.pl > samples.tsv.inferred
if [ -d ./lucene_full_standard ]; then
	rm -rf lucene_full_standard
	rm -rf lucene_full_ws
fi
cat samples.tsv | python $scripts/../lucene_indexer.py samples.tsv.inferred > lucene.indexer.run 2>&1
head -1 samples.tsv | perl -ne 'BEGIN { print "index\tfield_name\n";} chomp; for $e (split(/\t/,$_)) { print "".$i++."\t$e\n";}' > samples.fields.tsv
