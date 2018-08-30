# Use an official Python runtime as a base image
FROM debian

# Install basics
RUN apt-get update && apt-get install -y \
    python2.7 \
    python-dev \
    python-pip \
    tabix \
    sqlite3 \
    git \
    curl \
    wget \
    default-jdk \
    ant

# cribbed from https://bitbucket.org/coady/docker/src/tip/pylucene/Dockerfile
WORKDIR /usr/src/pylucene
RUN curl https://www.apache.org/dist/lucene/pylucene/pylucene-6.5.0-src.tar.gz \
    | tar -xz --strip-components=1
RUN cd jcc \
    && JCC_JDK=/usr/lib/jvm/default-java python setup.py install
RUN make all install JCC='python -m jcc' ANT=ant PYTHON=python NUM_FILES=8

WORKDIR ..
RUN rm -rf pylucene

# Copy the current directory contents 
# (i.e. Snaptron top-level directroy) into the container at /snaptron
# this is just to boot strap deployment (eases development)
# the actual Snaptron will be git cloned in the externally mounted "/deploy"
ADD . /snaptron/

# clone master branch of Snaptron
RUN pip install -r /snaptron/requirements.txt

# Make Snaptron ports available to the world outside this container
EXPOSE 1556 1557 1558 1585 1587 1590 1591 1592 1593 1594 1595

# Define environment variable
ENV NAME World

ENTRYPOINT ["/snaptron/entrypoint.sh"]
CMD []
