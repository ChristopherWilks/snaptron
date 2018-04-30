#!/bin/bash
#a generic setup from Rail raw junction output to Snaptron instance
#must have >=1.2.1 versions of: tabix, bgzip, and bgzip_uncompressed in the path
#bgzip_uncompressed can be had from:
#http://snaptron.cs.jhu.edu/data/htslib-1.2.1_nocomp.tar.gz

#also assumes this script will be called from the Snaptron server checkout root
#as it uses that assumption to find the other scripts it needs
#and metadata tsv should be named "samples.tsv" and be in the current directory

#args:
#1) path to Rail's cross-sample junction call file (junctions.tsv.gz)
#2) path to bowtie index of origin genome
#3) path to directory of already downloaded annotation GTFs from UCSC's table browser
#	or the path to a already ripped annotations file 
#	(must be gzipped with .gz at the end of the filename)
#4) new data source ID (check current set of compilations to know which to use)
#5) [optional] argument to use the uncompressed version of Tabix (pass a 1)

#get the snaptron checkout root dir (assuming the script is called from there)
#should be the deploy subdirectory
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`
root=$scripts/../
source $root/python/bin/activate

#this takes in as --input-file the "raw" cross-sample junctions output from rail
python $scripts/convert_rail_raw_cross_sample_junctions.py --data-src $4 --input-file $1 --bowtie-idx $2 | bgzip > junctions.tsv.snap.bgz

#setup metadata with proper IDs (assume it's already named samples.tsv)
#assumes 1) (SRR) Run is the first column in the samples.tsv file
#and 2) that junctions.tsv.gz.samples2ids has been provided ahead of time (format: rail_id<TAB>SRR)
mv samples.tsv samples.tsv.orig
#pick off the header for later
head -1 samples.tsv.orig | perl -ne '$s=$_; $s=~s/,/\t/g; print "rail_id\t$s";' > samples.tsv
cat samples.tsv.orig | egrep -v -e '^Run,' | sort -t',' -k1,1 | perl -ne '$s=$_; $s=~s/,/\t/g; print "$s";' > samples.tsv.sorted

sort -k2,2 junctions.tsv.gz.samples2ids > junctions.tsv.gz.samples2ids.sorted

join -t'	' -1 2 -2 1 junctions.tsv.gz.samples2ids.sorted samples.tsv.sorted > j1
cut -f 2 j1 > j1a
cut -f 1,3- j1 > j1b
paste j1a j1b  | sort -k1,1n >> samples.tsv
rm j1 j1a j1b


#To get the raw annotation GTFs:
#1) select each of the various annotations you want from the UCSC genome browser table browser interface 
#2) choose GTF as output format)
#3) then save them all to the path for --annotations specified below

#check to see if the user passed in a pre-ripped collected annotations file
#if so, just symlink that and run the next step
p=`perl -e '$s="'$3'"; @p=split(/\./,$s); $p=pop(@p); print "$p\n";'`
echo $p
if [ $p == 'gz' ]; then
	ln -fs $3 ./ripped_annotations.tsv.gz
else
	python $root/annotations/rip_annotated_junctions.py --extract-script-dir $root --annotations $3 | gzip > ripped_annotations.tsv.gz
fi

#annotate and build final snaptron
zcat junctions.tsv.snap.bgz | cut -f2,3,4,6,8,9,12- | python $root/annotations/process_introns.py --annotations ripped_annotations.tsv.gz | bgzip > junctions.bgz
rm junctions.tsv.snap.bgz

tabix -s 2 -b 3 -e 4 junctions.bgz

#build uncompressed version of BGZipped Tabix index for speed
if [ -z ${5+v} ]; then
        echo "sticking with compressed junctions file"
        ln -fs junctions.bgz junctions_uncompressed.bgz
else
#The compress_level=0 modified bgzf must be in your path before any standard bgzf binaries
        echo "creating uncompressed junctions file"
        zcat junctions.bgz | bgzip > junctions_uncompressed.bgz
fi
tabix -s 2 -b 3 -e 4 junctions_uncompressed.bgz

#build junctions.sqlite
if [ -f ./junctions.sqlite ]; then
	rm ./junctions.sqlite
fi
$scripts/build_sqlite_junction_db.sh junctions junctions.bgz

#build Lucene metadata indices (assumes samples.tsv is present and is sorted by rail_id in ascending order)
perl -e 'print "rail_id\tjunction_count\tjunction_coverage\tjunction_avg_coverage\n";' > jx_stats_per_sample.tsv
zcat junctions.bgz | cut -f 12 | perl -ne 'chomp; @f=split(/,/,$_); shift(@f); for $f (@f) { ($f,$c)=split(/:/,$f); $count{$f}++; $cov{$f}+=$c; } END { for $f (keys %count) { $avg=$cov{$f}/$count{$f}; print "$f\t".$count{$f}."\t".$cov{$f}."\t$avg\n";}}' | sort -t'	' -k1,1n >> jx_stats_per_sample.tsv
paste samples.tsv <(cut -f 2- jx_stats_per_sample.tsv) > samples.jx.tsv
mv samples.jx.tsv samples.tsv
cat samples.tsv | perl $scripts/infer_sample_metadata_field_types.pl > samples.tsv.inferred
if [ -d ./lucene_full_standard ]; then
	rm -rf lucene_full_standard
	rm -rf lucene_full_ws
fi
cat samples.tsv | python $scripts/../lucene_indexer.py samples.tsv.inferred > lucene.indexer.run 2>&1
head -1 samples.tsv | perl -ne 'BEGIN { print "index\tfield_name\n";} chomp; for $e (split(/\t/,$_)) { print "".$i++."\t$e\n";}' > samples.fields.tsv
