# Use an official Python runtime as a base image
FROM debian

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
    default-jdk

#clone master branch of Snaptron
RUN git clone https://github.com/ChristopherWilks/snaptron.git

# This will setup Snaptron with the SRAv2 compilation which contains
# the system tests.  This includes installing additional python packages,
# PyLucene (including the JCC), and linking the srav2-specific snaptron
# configuration file (snapconf.py).
# It will also copy down the required backing databases and indices.
# This latter step takes minutes-to-a-few-hours depending on the network/disk
# speed due to copying down ~70GBs data.
RUN cd snaptron ; ./deploy/deploy_snaptron.sh srav2

# Make port 80 available to the world outside this container
EXPOSE 1555 1556 1557 1558 1580

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "./snaptron/snaptron_server --no-daemon"]
