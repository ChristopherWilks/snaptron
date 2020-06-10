# Snaptron
fast webservices based query tool for searching exon-exon splice junctions and related sample metadata

**Ask questions in the project's**

[![Join the chat at https://gitter.im/snaptron/Lobby](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/snaptron/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

## User Guide ##
http://snaptron.cs.jhu.edu

## Deployment ##

We recommend using the Snaptron under Docker, rather than attempting a full installation due to the number of dependencies and the complexity of configuration.

A base docker image exists primarily for testing but which includes a full working install of Snaptron and its dependencies:

https://quay.io/repository/broadsword/snaptron?tab=tags

The following are the quick 'n dirty Docker + Singularity commands you can use to git clone the latest Snaptron server code, checkout the compilation of your choice, and get it running w/o any trimmings.

We use `encode1159` as a relatively small (~9 GBs), but real world, human compilation example.

While the example is relatively small, it will take several minutes to run, please be patient.

### Pull the image ###

Docker:

`docker pull quay.io/broadsword/snaptron:latest`

Singularity:

`singularity pull docker://quay.io/broadsword/snaptron:latest`

### Clone latest Snaptron code and deploy compilation ###

The actual code to run Snaptron server and the data/indexes themeslves are *not* included in the Snaptron container image.
This is for flexibility in updates for the server code and the size of most of the data backing Snaptron compilations is prohibitively large.  

This means the Snaptron image is only for convenience in setting up the environment to run Snaptron server, it is *not* for reproducibility since it doesn't capture the state of the Snaptron server code at any time.

The following command will use the Snaptron container to clone the Snaptron server code and download/setup the compilation on a local filesystem on the host OS bind mounted into the container:

Docker:

```docker run --rm -i -t --name snaptron_encode1159 --volume /path/to/host/deploy:/deploy:rw quay.io/broadsword/snaptron deploy encode1159```

Singularity:

```singularity exec -B /path/to/host/deploy:/deploy <snaptron_img_name>.simg /bin/bash -x -c "/snaptron/entrypoint.sh deploy encode1159"```

Singularity only: `<snaptron_img_name>` is the prefix for the Singularity filename.

You will need to change `/path/to/host/deploy` to a real full path on the *host* (not container) that will be used to store the compilation data and the Snaptron server code.  This should have enough capacity for encode1159 >= 20 GBs.

Most other compilations will require much more space, on the order of 50-200 GBs.

### Run the Docker image on previously deployed compilation ###

Docker:

```docker run --rm -p 21587:1587 -i -t --name snaptron_encode1159 --volume /path/to/host/deploy:/deploy:rw quay.io/broadsword/snaptron run encode1159```

Only for Docker: `-p 21587:1587` sets the container internal port which Snaptron is hosted on (1587) to map to the external port on the host OS of 21587.

You can change the 21587 to any available port you like, this is the port you will connect to Snaptron on, e.g. to test:

Singularity:

```singularity exec -B /path/to/host/deploy:/deploy <snaptron_img_name>.simg /bin/bash -x -c "/snaptron/entrypoint.sh run encode1159"```

`/path/to/host/deploy` is the same in all Docker/Singularity commands.

Test:

`curl http://localhost:<port>/snaptron?regions:CD99` 

to get the jx's within the coordinates of the CD99 gene from the local container hosted Snaptron server you just started.

(where `<port>` is either 21587 for the Docker image or 1587 for the Singularity image)

## Full Installation Instructions ##

	git clone https://github.com/ChristopherWilks/snaptron.git

NOTE: Avoid setting Snaptron up on a Lustre or NFS filesystem
since Snaptron's reliance on SQLite may cause problems on those systems.

To setup an instance based on a particular compilation (srav1, srav2, gtex, tcga):

	./deploy_snaptron.sh srav1

This process will take at least 10's of minutes and may
go for an hour or more depending on your bandwidth, storage,
and compute capacity.

It has to build all the dependencies, download all the source data, 
and create multiple indices.

For the largest of the compilations (srav2) the final data
footprint will be ~75 gigabytes on disk.  About 54 gigabytes
of this is in the SQLite database which is 
created locally once the raw data has been downloaded from 
the Snaptron server.  The data transfer is therefore ~20 gigabytes.

The PyLucene install in particular requires extensive 
dependencies and several minutes to build.  Through
it will display various errors and warnings.  These
are not critical as long as it ends with this output:

> Finished processing dependencies for lucene==4.10.1

### Enabling uncompressed Tabix ###

To enable the uncompressed version of the Tabix indices (faster than compressed), 
you must first download our modified version of 
[HTSlib 1.2.1] (http://snaptron.cs.jhu.edu/data/htslib-1.2.1_nocomp.tar.gz)
source which sets the compression level to 0 (no compression).

You must build the source and make sure the resulting bgzip binary is before any
other bgzip versions in your PATH.

Then run the above script with an additional argument:

	./deploy_snaptron.sh srav1 1

## Running the Snaptron server ##

within the snaptron working directory:

	source python/bin/activate
	python ./srav1_snaptron_server --no-daemon

The Snaptron server defaults to port 1555 on localhost.

## Tests ##

Snaptron has both unit tests and system tests ("round trip testing").
These only work for the SRAv1 and SRAv2 compilations.

In a separate terminal in the Snaptron working directory run:

### Unit Tests ###

	source ./python/bin/activate
	python ./test_snaptron.py

### System Tests ###

These require the Snaptron server to be running.

	./tests.sh 1

The system tests use file diffing to determine if
the services are working correctly.
