#!/usr/bin/env bash
set -eo pipefail
dir=$(dirname $0)
COMPILATION_JXN2STUDIES_PATHS_FILE=${dir}/compilation_jxn2studies_paths.tsv
TABIX=/datascope/recount03/miniconda3e1/bin/tabix

#e.g. "compilation=gtexv2&jid=5&chrom=chr4"
query=$1

#e.g. compilation=gtexv2&jid=5&chrom=chr4
compilation=$(echo "$query" | tr $'&' $'\n' | fgrep "compilation=" | cut -d'=' -f2)
jid=$(echo "$query" | tr $'&' $'\n' | fgrep "jid=" | cut -d'=' -f2)
chrom=$(echo "$query" | tr $'&' $'\n' | fgrep "chrom=" | cut -d'=' -f2)

#TODO: look up jxn2studies file for 1) compilation and 2) chromosomes and then query it with jxnID
cpath=$(fgrep $'\t'"$compilation"$'\t' $COMPILATION_JXN2STUDIES_PATHS_FILE | cut -f 3)
#NOTE: leaves no files on disk for now
msg=$($TABIX $cpath/${chrom}.jxn2studies.gz ${jid}:1-1 | cut -f 3- | perl $dir/decorate_studies.pl "$compilation" "$jid")
#msg=$($TABIX $cpath/${chrom}.jxn2studies.gz ${jid}:1-1 2>/dev/null)
#msg="$TABIX $cpath/${chrom}.jxns2studies.gz ${jid}:1-1 2>/dev/null"
##based liberally on:
#https://github.com/hhsnopek/beeroclock/blob/master/service.sh
  #msg="HELLOOOO\r"
  #link="https://trace.ncbi.nlm.nih.gov/Traces/?view=study&acc=ERP001942"
  #msg="<html><head></head><body style='font-family: monospace; font-size: 32px;'><p>$link</p></body></html>\r"
  echo "HTTP/1.1 200 OK"
  echo "Connection: close"
  #echo "Content-Type: text/plain; charset=utf-8"
  echo "Content-Type: text/html; charset=utf-8"
  echo "Content-Length: ${#msg}"
  echo "Host: snaptron.cs.jhu.edu"
  echo "Date: $(TZ=UTC; date '+%a, %d %b %Y %T GMT')"
  echo -e "\n${msg}"
exit 0

    
#printf 'Internal Error: No Content-Type passed into buildRespBody.\nPlease file an issue here https://github.com/hhsnopek/beerokclock with the current URL.\nThank you!\r'
