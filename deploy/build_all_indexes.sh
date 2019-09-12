#!/usr/bin/env bash
set -o pipefail -o nounset -o errexit 
date=`date +%Y%m%d_%S`

export LC_ALL=C 

#e.g. output from Monorail's merge step
#fully formattted acording to Snaptron's spec (TAB delimited), gzipped:
#snaptron_id,chrom,start,end,length,strand,annotated,left_motif,right_motif,left_annoated,right_annotated,samples,samples_count,coverage_sum,coverage_avg,coverage_median,data_source_id
junctions=$1
tmpdir=$2
#TSV of sample metadata starting with rail_id integer as first column
samples=$3

basedir=$(dirname $0)
#only build compressed junction table & sqlite db (skip uncompressed by default)
/bin/bash -x $basedir/rebuild_junctions.sh $junctions $tmpdir

#make a backup of original samples file
rsync -av $samples ${samples}.${date}
if [[ $samples != "samples.tsv" ]]; then
    ln -s $samples samples.tsv
fi

/bin/bash -x $basedir/build_lucene_indexes.sh all
