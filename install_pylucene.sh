#modified from http://stackoverflow.com/questions/24278627/building-pylucene-on-ubuntu-14-04trusty-tahr

source python/bin/activate

# Downloads and extract pylucene
wget http://mirror.serversupportforum.de/apache/lucene/pylucene/pylucene-4.10.1-1-src.tar.gz
tar -zxvf pylucene-4.10.1-1-src.tar.gz

# Install dependencies
#This REQUIRES ant, g++, python-dev, and Java >=1.7
#sudo apt-get install ant
#sudo apt-get install g++
#sudo apt-get install python-dev
#sudo apt-get install python3-setuptools
easy_install pip
pip install setuptools --upgrade 

cd pylucene-4.10.1-1/jcc
python setup.py build
python setup.py install
cd ..

# Build and install pylucene
make
easy_install ./dist/lucene-4.10.1-py2.7-linux-x86_64.egg
cd ..
