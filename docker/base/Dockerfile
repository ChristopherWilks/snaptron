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
    sqlite3

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 1555 1556 1557 1558 1580

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "snaptron_server"]
