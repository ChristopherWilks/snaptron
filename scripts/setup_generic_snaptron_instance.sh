#!/bin/bash

#currently using the mm10 Mouse build as a concrete example of
#a generic setup from Rail raw junction output to Snaptron instance

#this takes in as --input-file the "raw" cross-sample junctions output from rail
python convert_rail_raw_cross_sample_junctions.py --data-src 5 --input-file junctions.tsv.gz --bowtie-idx /data3/indexes/mm10/genome | bgzip > junctions.tsv.snap.bgz

#UCSC, GENCODE (and possibly the M9 and M11 variants?), RefSeq
#grab GTFs of the various annotations you want from the UCSC genome browser table browser interface (choose GTF as output format)
#then save them all to the path for --annotations specified below
python rip_annotated_junctions.py --extract-script-dir ../ --annotations /data3/snaptron/mouse95_data/annotations > mouse10_ripped_annotations.tsv

#annotate and build final snaptron
zcat junctions.tsv.snap.bgz | cut -f2,3,4,6,8,9,12- | pypy /data/gigatron/snaptron/annotations/process_introns.py --annotations annotations/mouse10_ripped_annotations.tsv.gz | bgzip > junctions.tsv.snap.annots.bgz

tabix -s 2 -b 3 -e 4 junctions.tsv.snap.bgz

#build uncompressed version of BGZipped Tabix index for speed
zcat junctions.tsv.snap.bgz | ~/bgzip > junctions.tsv.snap.uncompressed.bgz
tabix -s 2 -b 3 -e 4 junctions.tsv.snap.uncompressed.bgz

#build junctions.sqlite
/data/gigatron/snaptron/scripts/build_sqlite_junction_db.sh junctions junctions.tsv.snap.bgz
