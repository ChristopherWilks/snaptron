#!/bin/bash
#Deploys snaptron for whatever data source label was passed in (srav1,srav2,tcga,gtex)

#Tabix, Sqlite3, and virtualenv need to be compiled and already in the PATH *before*
#running this script

#setup python for Snaptron
virtualenv ./python
source ./python/bin/activate
pip install -r dependencies.txt

#this requires sudo and may need additional
#packages at the system level
./install_pylucene.sh

#link config file(s)
./setup_configs.sh ${1}

#grab data
mkdir data
cd data
wget http://snaptron.cs.jhu.edu/data/${1}/samples.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/junctions.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/all_transcripts.gtf.bgz
wget http://snaptron.cs.jhu.edu/data/${1}/refseq_transcripts_by_hgvs.tsv
wget http://snaptron.cs.jhu.edu/data/${1}/ucsc_known_canonical_transcript.tsv

#creation of Tabix index of junctions and all_transcripts
tabix -s 2 -b 3 -e 4 junctions.bgz
tabix -s 1 -b 4 -e 5 all_transcripts.gtf.bgz

#creation of sqlite junction db
../scripts/build_sqlite_junction_db.sh junctions junctions.bgz
#creation of sample2junction of sqlite by_sample_id db
../scripts/build_sqlite_sample_mapping_db.sh sample2junction junctions.bgz

#run lucene indexer on metadata
cat samples.tsv | perl -ne 'chomp; $n++; @f=split(/\t/,$_); foreach $idx (0 .. (scalar @f)-1) { $type="t"; $type="n" if($f[$idx] eq "NA"); if($f[$idx]=~/^-?\d+?\.?\d+$/) { $type="f"; } $type="i" if($f[$idx]=~/^-?\d+$/); $counts{$idx}->{$type}++; } END { foreach $idx (sort { $a<=>$b} keys %counts) { print "$idx"; $counts{$idx}->{"n"}=-$counts{$idx}->{"n"} if(defined($counts{$idx}->{"n"})); $counts{$idx}->{"i"}=-$counts{$idx}->{"i"} if(defined($counts{$idx}->{"f"}) && defined($counts{$idx}->{"i"}) > 0); foreach $t (sort {$counts{$idx}->{$b}<=>$counts{$idx}->{$a}} keys %{$counts{$idx}}) { print "\t$t,".$counts{$idx}->{$t}; } print "\n";}}' > samples.tsv.type_inference
cat samples.tsv | python ../lucene_indexer.py samples.tsv.type_inference
