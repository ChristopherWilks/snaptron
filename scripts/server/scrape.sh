#first just get all Snaptron service accesses
fgrep "?region" apache_logs/access.log > all_snaptron_service_accesses.log

#get counts of accesses per unique IP for each month/year
cat all_snaptron_service_accesses.log | sed 's/ /\//g' | cut -d'/' -f 1,5,6 | cut -d':' -f 1 | sort | uniq -c | sort -t'/' -k3,3n -k2,2M | fgrep -v "128.220.35.129" > access.log.snaptron_all.ip_month_year.c.sorted

#now get counts of unique IPs per month over the years
cut -d'/' -f 2,3 access.log.snaptron_all.ip_month_year.c.sorted | sed 's/^/\//' | sort | uniq -c | sort -t'/' -k3,3n -k2,2M > access.log.snaptron_all.ip_month_year.uniq.c

#get total unique IPs overall months/years
cat access.log.snaptron_all.ip_month_year.uniq.c | tr -s " " \\t | cut -f 2 | numsum
