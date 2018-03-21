d=`curl "http://localhost:${1}/snaptron?regions=chr17:43045629-43125483&header=0" 2>/dev/null | head -1 | perl -ne 'chomp; @f=split(/\t/,$_); $f[12]=~/^,(\d+):/; print "$1";'`
curl "http://localhost:${1}/snaptron?regions=chr17:43045629-43125483&sfilter=rail_id:$d" | head
d=`curl "http://localhost:${1}/snaptron?regions=BRCA1&header=0" 2>/dev/null | head -1 | perl -ne 'chomp; @f=split(/\t/,$_); $f[12]=~/^,(\d+):/; print "$1";'`
curl "http://localhost:${1}/snaptron?regions=BRCA1&sfilter=rail_id:$d" | head
