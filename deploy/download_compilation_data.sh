#!/bin/bash
#Downloads and indexes data for a specific compilation
#This assumes that the origin server (snaptron.cs.jhu.edu) is online

#compilation
COMP=$1
DATA_DIR=${2}

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "../".join("/",@f)."\n";'`
echo "scripts dir: $scripts"

#assume ./data already exists
cd $DATA_DIR
#echo "+++Downloading snaptron data, this make take a while..."
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/samples.tsv
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/samples.fields.tsv
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/samples.groups.tsv

echo "+++Creating Lucene indices"
#run lucene indexer on metadata
cat samples.tsv | perl ${scripts}/infer_sample_metadata_field_types.pl > samples.tsv.type_inference
cat samples.tsv | python ${scripts}/../lucene_indexer.py samples.tsv.type_inference > run_indexer 2>&1

echo "+++Downloading data and creating SQLite DBs"
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/junctions.bgz
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/junctions.bgz.tbi
if [ -e junctions.sqlite ]; then
    rm junctions.sqlite
fi

#reindex in SQLite to avoid cost of downloading uncompressed junction db
${scripts}/build_sqlite_db.sh junctions junctions.bgz

wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/genes.bgz
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/genes.bgz.tbi
if [ -e genes.sqlite ]; then
    rm genes.sqlite
fi
${scripts}/build_sqlite_db.sh genes genes.bgz

wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/exons.bgz
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/exons.bgz.tbi
if [ -e exons.sqlite ]; then
    rm exons.sqlite
fi
#${scripts}/build_sqlite_db.sh exons exons.bgz

wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/all_transcripts.gtf.bgz
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/all_transcripts.gtf.bgz.tbi
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/refseq_transcripts_by_hgvs.tsv
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/ucsc_known_canonical_transcript.tsv
wget -nc http://snaptron.cs.jhu.edu/data/${COMP}/gencode.v25.annotation.gff3.gz

ln -fs junctions.bgz junctions_uncompressed.bgz
ln -fs junctions.bgz.tbi junctions_uncompressed.bgz.tbi

cd ../
ln -fs data/lucene_indexed_numeric_types.tsv
