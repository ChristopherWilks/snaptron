#!/usr/bin/env bash
set -o pipefail -o nounset -o errexit 
date=`date +%Y%m%d_%S`

export LC_ALL=C 

#e.g. output from Monorail's merge step
#fully formattted acording to Snaptron's spec (TAB delimited), gzipped:
#snaptron_id,chrom,start,end,length,strand,annotated,left_motif,right_motif,left_annoated,right_annotated,samples,samples_count,coverage_sum,coverage_avg,coverage_median,data_source_id
#OR
#a suffix such as ".sorted.gz" if $doall == "all"
infile_or_prefix=$1
tmpdir=$2
#TSV of sample metadata starting with rail_id integer as first column
samples=$3
#either "all" for exons,genes,junctions; or a specific entry from that list (e.g. "exons)
doall=$4

basedir=$(dirname $0)
if [[ "$doall" == "all" ]]; then
    #exons, junctions, genes
    for dtype in junctions exons genes ; do
        #only build compressed junction table & sqlite db (skip uncompressed by default)
        #for "all" assume $infile_or_prefix is the suffix with the appropriate type: e.g. exons.sorted.gz
        /bin/bash -x $basedir/rebuild_junctions.sh ${dtype}${infile_or_prefix} $tmpdir $dtype
    done
else
    /bin/bash -x $basedir/rebuild_junctions.sh $infile_or_prefix $tmpdir $doall
fi


#make a backup of original samples file
rsync -av $samples ${samples}.${date}
if [[ $samples != "samples.tsv" ]]; then
    ln -s $samples samples.tsv
fi

/bin/bash -x $basedir/build_lucene_indexes.sh all
