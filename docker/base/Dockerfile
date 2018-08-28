# Use an official Python runtime as a base image
FROM debian

# If the user passes in 1) a compilation and 2) a data directory
# 2) is only used if 1) is passed in
ARG COMPILATION
ARG DATA_DIR

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

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

# clone master branch of Snaptron
RUN git clone https://github.com/ChristopherWilks/snaptron.git
RUN pip install -r snaptron/requirements.txt
RUN touch snaptron/FINISHED_DEPENDENCIES

# setup compilation if passed in
# if DATA_DIR was also passed, assume all compilation data has already been downloaded
RUN if [ "y$COMPILATION" != "y" ] ; then \
	cd snaptron ; ./deploy/deploy_snaptron.sh $COMPILATION $DATA_DIR ; fi

# Make Snaptron ports available to the world outside this container
EXPOSE 1556 1557 1558 1585 1587 1590 1591 1592 1593 1594 1595

# Define environment variable
ENV NAME World

CMD ["/bin/bash"]
