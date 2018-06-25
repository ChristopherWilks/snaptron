#!/bin/bash
#parameters:
#1: directory containing Snaptron backing data
#2: starting index (e.g. after last used ID from previous compilation)

if [[ $1 = `pwd` || $1 = './' ]]; then
	echo "DO NOT run in the same directory as the original data; exiting"
	exit -1
fi

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

for t in junctions genes exons
do
	zcat ${1}/${t}.bgz | perl -ne 'chomp; @f=split(/\t/,$_); $f[11]=~s/^,//; $n=""; for $a (split(/,/,$f[11])) { ($sid,$c)=split(/:/,$a); $sid+='${2}'; $n.=",$sid:$c"; } $f[11]=$n; print "".join("\t",@f)."\n";' | bgzip > ${t}.bgz
	tabix -s 2 -b 3 -e 4 ${t}.bgz
	/bin/bash -x ${p}/build_sqlite_junction_db.sh ${t} ${t}.bgz
done
cat ${1}/samples.tsv  | perl -ne 'chomp; $f=$_; if($f=~/rail_id/) { print "$f\n"; next; } @f=split(/\t/,$f); $f[0]+='${2}'; print "".join("\t",@f)."\n";' > samples.reassigned.tsv
