#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)
#1: Snaptron name of compilation (e.g. srav2)
#2 (optional): 1 if we should generate the uncompressed version of the junctions database (for performance)

#./deploy/deploy_snaptron.sh srav2 1

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`
/bin/bash -x ${scripts}/deploy_snaptron_nodata.sh ${1}

#grab data
mkdir data
cd data
#echo "+++Downloading snaptron data, this make take a while..."
wget http://snaptron.cs.jhu.edu/data/${1}/samples.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/junctions.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/all_transcripts.gtf.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/refseq_transcripts_by_hgvs.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/ucsc_known_canonical_transcript.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/gencode.v25.annotation.gff3.gz

echo "+++Creating Tabix index on transcripts file"
#creation of Tabix index of all_transcripts
tabix -s 1 -b 4 -e 5 all_transcripts.gtf.bgz

echo "+++Creating SQLite DB of junctions"
#creation of sqlite junction db
${scripts}/build_sqlite_junction_db.sh junctions junctions.bgz

echo "+++Creating Lucene indices"
#run lucene indexer on metadata
cat samples.tsv | perl ${scripts}/infer_sample_metadata_field_types.pl > samples.tsv.type_inference
cat samples.tsv | python ${scripts}/../lucene_indexer.py samples.tsv.type_inference > run_indexer 2>&1

echo "+++Creating Tabix index on junctions file"
if [ -z ${2+v} ]; then
        echo "sticking with compressed junctions file"
        ln -s junctions.bgz junctions_uncompressed.bgz
else
#The compress_level=0 modified bgzf must be in your path before any standard bgzf binaries
        echo "creating uncompressed junctions file"
        zcat junctions.bgz | bgzip > junctions_uncompressed.bgz
fi

tabix -s 2 -b 3 -e 4 junctions_uncompressed.bgz

cd ../
ln -s data/lucene_indexed_numeric_types.tsv
