#!/usr/bin/env bash
set -o pipefail -o nounset -o errexit 
date=`date +%Y%m%d_%S`

#short compilation name (e.g. tcga)
compilation=$1
#e.g. output from Monorail's merge step
#fully formattted acording to Snaptron's spec (TAB delimited), gzipped:
#snaptron_id,chrom,start,end,length,strand,annotated,left_motif,right_motif,left_annoated,right_annotated,samples,samples_count,coverage_sum,coverage_avg,coverage_median,data_source_id
junctions=$2
#TSV of sample metadata starting with rail_id integer as first column
samples=$3

basedir=$(dirname $0)
#only build compressed junction table & sqlite db (skip uncompressed by default)
/bin/bash -x $basedir/rebuild_junctions.sh $compilation $junctions
mv junctions.ordered.bgz junctions.bgz

#make a backup of original samples file
rsync -av $samples ${samples}.${date}
if [[ $samples != "samples.tsv" ]]; then
    ln -s $samples samples.tsv
fi

/bin/bash -x $basedir/build_lucene_indexes.sh all
