#!/bin/bash
#Downloads and indexes data for a specific compilation
#This assumes that the origin server (snaptron.cs.jhu.edu) is online

#compilation
COMP=$1
UNCOMPRESSED_JX=$2

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`

#assume ./data already exists
cd data
#echo "+++Downloading snaptron data, this make take a while..."
wget http://snaptron.cs.jhu.edu/data/${COMP}/samples.tsv
wget http://snaptron.cs.jhu.edu/data/${COMP}/samples.groups.tsv
wget http://snaptron.cs.jhu.edu/data/${COMP}/junctions.bgz
wget http://snaptron.cs.jhu.edu/data/${COMP}/junctions.bgz.tbi
wget http://snaptron.cs.jhu.edu/data/${COMP}/genes.bgz
wget http://snaptron.cs.jhu.edu/data/${COMP}/genes.bgz.tbi
wget http://snaptron.cs.jhu.edu/data/${COMP}/exons.bgz
wget http://snaptron.cs.jhu.edu/data/${COMP}/exons.bgz.tbi
wget http://snaptron.cs.jhu.edu/data/${COMP}/all_transcripts.gtf.bgz
wget http://snaptron.cs.jhu.edu/data/${COMP}/all_transcripts.gtf.bgz.tbi
wget http://snaptron.cs.jhu.edu/data/${COMP}/refseq_transcripts_by_hgvs.tsv
wget http://snaptron.cs.jhu.edu/data/${COMP}/ucsc_known_canonical_transcript.tsv
wget http://snaptron.cs.jhu.edu/data/${COMP}/gencode.v25.annotation.gff3.gz

echo "+++Creating SQLite DBs"
${scripts}/build_sqlite_db.sh junctions junctions.bgz
${scripts}/build_sqlite_db.sh genes genes.bgz
${scripts}/build_sqlite_db.sh exons exons.bgz

echo "+++Creating Lucene indices"
#run lucene indexer on metadata
cat samples.tsv | perl ${scripts}/infer_sample_metadata_field_types.pl > samples.tsv.type_inference
cat samples.tsv | python ${scripts}/../lucene_indexer.py samples.tsv.type_inference > run_indexer 2>&1

echo "+++Creating Tabix index on junctions file"
if [ -z ${UNCOMPRESSED_JX+v} ]; then
        echo "sticking with compressed junctions file"
        ln -s junctions.bgz junctions_uncompressed.bgz
else
#The compress_level=0 modified bgzf must be in your path before any standard bgzf binaries
        echo "creating uncompressed junctions file"
        zcat junctions.bgz | bgzip > junctions_uncompressed.bgz
fi

tabix -s 2 -b 3 -e 4 junctions_uncompressed.bgz

cd ../
ln -fs data/lucene_indexed_numeric_types.tsv
