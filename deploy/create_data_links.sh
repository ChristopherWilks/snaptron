#!/bin/bash
#takes the path to the following files as the first argument
#and the path to the target data directory as the 2nd argument
#e.g. create_data_links.sh /data/snaptron_staging/encode /data/snaptron_data/encode
#$1 is the path to the directory elsewhere to link from (e.g. /data/snaptron_staging/encode)
#$2 is the directory to link into (e.g. /data/snaptron_data/encode)
#$3 is the genome reference (e.g. hg38, mm10)

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
ln -fs ${1}/samples.fields.tsv

ls ../gene_annotation_${3}/*gencode*.gff3.gz | perl -ne 'chomp; `ln -fs $_`;'
#needed by Snaptron whatever the genome reference type
ln -fs ../gene_annotation_hg38/ucsc_known_canonical_transcript.tsv
ln -fs ../gene_annotation_hg38/refseq_transcripts_by_hgvs.tsv

ln -fs ${1}/exons.sqlite
ln -fs ${1}/exons.bgz
ln -fs ${1}/exons.bgz.tbi
ln -fs ${1}/genes.sqlite
ln -fs ${1}/genes.bgz
ln -fs ${1}/genes.bgz.tbi

ln -fs ${1}/bases
