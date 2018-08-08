#!/bin/bash
#creates a Python2 virtual environment and
#installs Python and PyLucene specific dependencies
#no params

#get the path to this script
scripts=`perl -e '@f=split(/\//,"'${0}'"); pop(@f); print "".join("/",@f)."\n";'`

echo "+++Setting up Python for Snaptron"
#setup python for Snaptron
#from https://virtualenv.pypa.io/en/stable/installation/
wget https://pypi.python.org/packages/source/v/virtualenv/virtualenv-13.1.2.tar.gz
tar xvfz virtualenv-13.1.2.tar.gz
cd virtualenv-13.1.2
python virtualenv.py ../python
cd ..
source ./python/bin/activate
pip install -r requirements.txt

echo "+++Setting up PyLucene and dependencies (this requires sudo)"
#this requires additional packages at the system level
/bin/bash -x ${scripts}/install_pylucene.sh

touch ./FINISHED_DEPENDENCIES
