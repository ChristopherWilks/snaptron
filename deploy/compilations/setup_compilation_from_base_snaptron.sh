#!/bin/bash
#assume we're in the working directory where all compilations are subdirs
#and that the master branch of the snaptron repo has been cloned into
#./snaptron

mkdir ${1}_snaptron
cd ${1}_snaptron

#get this script's path
p=`perl -e '@f=split("/","'$0'"); pop(@f); print "".join("/",@f)."\n";'`

#establish links from the original snaptron clone for a compilation
ls ../$p/../*.py | grep -v "test" | perl -ne 'chomp; $s=$_; `ln -fs $s`;'

ln -f ../$p/../snaptron_server ./${1}_snaptron_server
ln -fs ../$p/../instances/snapconf.py.${1} ./snapconf.py

#need the snaptron_data directory specific to this compilation
#to be already setup and passed in
ln -fs $2 ./data
ln -fs ../$p/../python
