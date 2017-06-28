#!/bin/bash
#a generic setup from Rail raw junction output to Snaptron instance
#must have >=1.2.1 versions of: tabix, bgzip, and bgzip_uncompressed in the path
#bgzip_uncompressed can be had from:
#http://snaptron.cs.jhu.edu/data/htslib-1.2.1_nocomp.tar.gz

#also assumes this script will be called from the Snaptron server checkout root
#as it uses that assumption to find the other scripts it needs
#and metadata tsv should be named "samples.tsv" and be in the current directory

#args:
#1) path to bowtie index of origin genome
#2) path to directory of already downloaded annotation GTFs from UCSC's table browser
#3) new data source ID (check current set of compilations to know which to use)

#get the snaptron checkout root dir (assuming the script is called from there)
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`
root=$scripts/../
source $root/python/bin/activate

#this takes in as --input-file the "raw" cross-sample junctions output from rail
python $scripts/convert_rail_raw_cross_sample_junctions.py --data-src $3 --input-file junctions.tsv.gz --bowtie-idx $1 | bgzip > junctions.tsv.snap.bgz

#To get the raw annotation GTFs:
#1) select each of the various annotations you want from the UCSC genome browser table browser interface 
#2) choose GTF as output format)
#3) then save them all to the path for --annotations specified below
python $root/annotations/rip_annotated_junctions.py --extract-script-dir $root --annotations $2 | gzip > ripped_annotations.tsv.gz

#annotate and build final snaptron
zcat junctions.tsv.snap.bgz | cut -f2,3,4,6,8,9,12- | pypy $root/annotations/process_introns.py --annotations ripped_annotations.tsv.gz | bgzip > junctions.bgz

rm junctions.tsv.snap.bgz

tabix -s 2 -b 3 -e 4 junctions.bgz

#build uncompressed version of BGZipped Tabix index for speed
zcat junctions.bgz | bgzip_uncompressed > junctions_uncompressed.bgz
tabix -s 2 -b 3 -e 4 junctions_uncompressed.bgz

#build junctions.sqlite
$scripts/build_sqlite_junction_db.sh junctions junctions.bgz

#build Lucene metadata indices
cat samples.tsv | perl $scripts/infer_sample_metadata_field_types.pl > samples.tsv.inferred
cat samples.tsv | python $root/lucene_indexer.py samples.tsv.inferred > lucene.indexer.run 2>&1 &

#TODO, need to move this file into the root of the snaptron compilation server
rsync -av lucene_indexed_numeric_types.tsv $root/
