export PORT=1300
mkdir $1
mkdir $1.bak
ln -s ../python $1/
rsync -av *.py $1/
cat snapconf.py | perl -ne 'chomp; $line=$_; $line="PORT=1300" if($line=~/^PORT=1555$/); print "$line\n";' > $1/snapconf.py 
rsync -av snaptron_server $1/
rsync -av test_s2i_ids_15.snaptron_ids $1/
rsync -av expected_ucsc_url $1/
rsync -av expected_ucsc_ids_url $1/
rsync -av expected_ucsc_format $1/
rsync -av expected_ucsc_ids_format $1/
cat ./tests.sh | perl -ne 'chomp; $s=$_; $s=~s/export PORT=1555/export PORT=1300/; print "$s\n";' > $1/tests.sh
export PATH=$PATH:/data2/kent_tools
ln -s /data2/gigatron2 $1/data
chmod a+x $1/tests.sh
