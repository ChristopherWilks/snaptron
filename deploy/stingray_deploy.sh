#!bin/bash

./deploy/create_data_links.sh $2 $3

ln -s ../snaptron/python
source ./python/bin/activate

ln -s $3 ./data
ln -s data/lucene_indexed_numeric_types.tsv

#link config file(s)
#YOU WILL NEED TO TAILOR THIS FILE TO YOUR COMPILATION's specific settings
ln -fs ./snaptron_server ./${1}_snaptron_server
rsync -av instances/snapconf.py.default instances/snapconf.py.${1}
ln -f instances/snapconf.py.${1} ./snapconf.py
