#!/bin/bash
#takes in Rail-RNA output coverage BigWigs
#and builds a consolidated TSV where each row is a genomic base
#and each column is a source samples (BigWig)

#assumes the samples.tsv file for this specific compilation is in the cwd
BWTOOL='./bwtool_mine2/bwtool'
ZSTDLIB='~/zstd-1.3.3/lib'
BGZIP_Z='~/bgzip_zstd'
TABIX_Z='~/tabix_zstd'

#$1 path to parent directory where all per-sample BigWigs are stored under (possibly multi-levels down)
#$2 path to directory of genomic region split files, a bwtool paste job will be created for each split file (e.g. /home-1/cwilks3@jhu.edu/work2/bigwig/hg38_splits/split_1m_14)
#$3 path to temporary output directory, should be a filesystem that can sustain multiple concurrent writes (e.g. on MARCC scratch Lustre, '/home-1/cwilks3\@jhu.edu/scratch/ct_h_s/bigwig', include the single quotes as well to properly handle the '@')
#$4 path to final output directory (e.g. on MARCC work-zfs, '/home-1/cwilks3\@jhu.edu/work2/sra/bigwig/finished')
#$5 prefix of job/compilation (e.g. 'sra')

OUTDIR=${3}
FINAL_DIR=${4}
PREFIX=${5}

mkdir bigwigs
cd bigwigs
find -L ${1} -name "*.bw" | egrep -v "\..\." | egrep -v "mean|median|unique" | perl -ne 'chomp; $f1=$_; @f=split(/\//,$f1); $f2 = pop(@f); `ln -s $f1`;'
#get rail_id,SRR,SRP to construct rail_id named links to the bigwig files
cut -f 1,2,22 ../samples.tsv | perl -ne 'chomp; ($rid,$srr,$srp)=split(/\t/,$_); `ln -fs $srp-$srr.bw $rid.bw`;'

cd ..

mkdir jobs
ls ${2}/* | perl -ne 'BEGIN { $s=""; open(IN,"<./samples.tsv"); @f=<IN>; chomp(@f); for $f (@f) { next if($f=~/rail_id/); ($f)=split(/\t/,$f); $s.=" bigwigs/$f.bw"; } close(IN); } chomp; $r=$_; $r=~/\/x(\d+)$/; $i=$1; if(length($i)==1) { $i="0".$i; } open(OUT,">./jobs/bw_paste_x$i.sh"); print OUT "#!/bin/bash -l\n#SBATCH\n#SBATCH --job-name='${PREFIX}'.$i\n#SBATCH --output=./.'${PREFIX}'.$i.out\n#SBATCH --error=./.'${PREFIX}'.$i.err\n#SBATCH --nodes=1\n#SBATCH --partition=parallel\n#SBATCH --mem=100G\n#SBATCH --time=36:00:00\n#SBATCH --ntasks-per-node=2\nexport LD_LIBRARY_PATH='${ZSTDLIB}':\$LD_LIBRARY_PATH\n'${BWTOOL}' paste --decimals=1 -fill=0 -regions=$r $s | '${BGZIP_Z}' > '${OUTDIR}'/x$i.bgzs\n'$TABIX_Z' -0 -s 1 -b 2 -e 3 '${OUTDIR}'/x$i.bgzs\nmv '${OUTDIR}'/x$i.bgzs* '${FINAL_DIR}'/\n"; close(OUT); `chmod a+x ./jobs/bw_paste_x$i.sh`; $i++;'
