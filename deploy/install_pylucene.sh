#modified from http://stackoverflow.com/questions/24278627/building-pylucene-on-ubuntu-14-04trusty-tahr
#PyLucene REQUIRES ant, g++, python-dev, and Java >=1.8 to already be installed
#for the Java requirement, you may be able to use java-7-openjdk-amd64 or a variant
#and in the environment; also that we're on an x86_64 machine
ARCH='x86_64'

source python/bin/activate

# Downloads and extract pylucene
wget https://www.apache.org/dist/lucene/pylucene/pylucene-4.10.1-1-src.tar.gz
tar -zxvf pylucene-4.10.1-1-src.tar.gz

# Install dependencies
easy_install pip
pip install setuptools --upgrade 

export JCC_JDK='/usr/lib/jvm/default-java'

cd pylucene-4.10.1-1/jcc
python setup.py build
python setup.py install
cd ..

#export LIBRARY_PATH=/usr/local/lib/python2.7/dist-packages/JCC-2.21-py2.7-linux-x86_64.egg

# Build and install pylucene
#the following assumes "ant" is in the path
cp Makefile Mafile.bak
echo 'ANT=ant' >> Makefile.new
echo 'PYTHON=../python/bin/python' >> Makefile.new
echo 'JCC=$(PYTHON) -m jcc.__main__ --shared --arch '"${ARCH}" >> Makefile.new
echo 'NUM_FILES=8' >> Makefile.new
cat Makefile >> Makefile.new
mv Makefile.new Makefile

#hack to get around shared issue with JCC
sed -i -e 's/SHARED=False/SHARED=True/' ../python/local/lib/python2.7/site-packages/JCC-2.21-py2.7-linux-x86_64.egg/jcc/config.py

make
make test
make install
cd ..
