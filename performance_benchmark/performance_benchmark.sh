#!/bin/bash -x

rsync -av ../*.py ./
ln -s ../data
. ../python/bin/activate

for i in {1..3} 
do 
	perl -e 'BEGIN { $FIN="./benchmark_queries.tsv"; print "Query.Size\tQuery.Time\tQuery.Type\n";} $tail=" >/dev/null 2>&1"; $M=2500000; $m1=$M*10; use Time::HiRes qw( tv_interval gettimeofday ); open(IN,"<$FIN"); %a; %h; while($line=<IN>) { chomp($line); ($m,$c)=split(/\t/,$line); $h{$c}=$m; push(@a,$c); } close(IN); for($i=$M;$i<=$m1;$i=$i+$M) { $n="chr1:1-$i"; ($n0)=split(/:/,$n); $n1=1; $n2=$i; for $q1 (@a) { $q=$q1; $m=$h{$q1}; $q=~s/:n:/$n/; $q=~s/:n0:/$n0/; $q=~s/:n1:/$n1/; $q=~s/:n2:/$n2/; $t=[gettimeofday]; `$q $tail`; $t2=[gettimeofday]; $interval = tv_interval($t,$t2); $i2=$i/100000; print "$i2\t$interval\t$m\n";  }}' > run${i}
done

paste run1 run2 run3 | grep -v -e 'Query' > run123
cat run123 | perl -ne 'BEGIN { print "Query.Size\tQuery.Time\tQuery.Type\n";} chomp; @f=split(/\t/,$_); $i=$f[0]; $r=$f[2]; $s=$f[1]+$f[4]+$f[7]; $s=$s/3; print "$i\t$s\t$r\n";' > run123_avg.tsv
