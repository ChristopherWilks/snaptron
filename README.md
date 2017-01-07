# Snaptron
fast webservices based query tool for searching exon-exon splice junctions and related sample metadata

## User Guide ##
http://snaptron.cs.jhu.edu

## Deployment ##

git clone git@github.com:ChristopherWilks/snaptron.git

NOTE: Avoid setting Snaptron up on a Lustre or NFS filesystem
since Snaptron's reliance on SQLite may cause problems on those systems.

To setup an instance based on a particular compilation (srav1, srav2, gtex, tcga):

> ./deploy_snaptron.sh srav1

This process will take at least 10's of minutes and may
go for an hour or more depending on your bandwidth, storage,
and compute capacity.

It has to build all the dependencies, download all the source data, 
and create multiple indices.

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

> ./deploy_snaptron.sh srav1 1

## Running the Snaptron server ##

within the snaptron working directory:

> source python/bin/activate

> python ./srav1_snaptron_server --no-daemon

The Snaptron server defaults to port 1555 on localhost.

## Tests ##

Snaptron has both unit tests and system tests ("round trip testing").

In a separate terminal in the Snaptron working directory run:

### Unit Tests ###
> source ./python/bin/activate

> python ./test_snaptron.py

### System Tests ###

These require the Snaptron server to be running.

> ./tests.sh 1

The system tests use file diffing to determine if
the services are working correctly.
