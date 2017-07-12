#!/bin/bash
#takes the path to the following files as the first argument
#and the path to the target data directory as the 2nd argument
#e.g. create_data_links.sh /data/snaptron_staging/encode /data/snaptron_data/encode

cd $2
ln -fs ${1}/junctions.bgz
ln -fs ${1}/junctions.bgz.tbi
ln -fs ${1}/junctions_uncompressed.bgz
ln -fs ${1}/junctions_uncompressed.bgz.tbi
ln -fs ${1}/junctions.sqlite
ln -fs ${1}/lucene_full_standard
ln -fs ${1}/lucene_full_ws
ln -fs ${1}/lucene_indexed_numeric_types.tsv
ln -fs ${1}/samples.tsv

ln -fs ../gene_annotation_hg38/ucsc_known_canonical_transcript.tsv
ln -fs ../gene_annotation_hg38/refseq_transcripts_by_hgvs.tsv
