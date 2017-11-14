.. Snaptron documentation Build file

.. |date| date::
.. |time| date:: %H:%M

Generated on |date| at |time|.

=====================================
Construction of Snaptron Compilations
=====================================

NOTE: this is a work in progress and at this time only meant for the most ambitious of users.

These instructions only cover setting up a new Snaptron compilation for junctions only,
not for existing Snaptron data on another server.

They also assume that Rail-RNA was the aligner OR that the input datafiles listed below
have been converted to the same as Rail's output formats.

This assumes that you already have in hand the following data files:

- Tab delimited file of raw junction sample coverage counts*
- Collection of one or more annotation GTFs (downloadable from UCSC Table Browser, e.g. RefSeq Human Genes).
  These will be used to determine which junctions are novel and which are annotated.
- Tab delimited sample metadata file with unique integer ID as the first column (`rail_id`)
  These integer IDs should be the same as the ones used in the junctions file above
- Bowtie index of source genome

\*The junctions file should have the following format (tab delimited) which is what Rail's `cross_sample_results/junctions.tsv.gz` is:

`header: blank sample1_name sample2_name ...
chromosome;strand;start;end sample1_read_count sample2_read_count sample3_read_count ...`

The samples MUST be in the same order in the junctions file as they are in the tab delimited sample metadata file,
otherwise the IDs will not be correct between the samples list and the junctions.

Snaptron Server Installation
----------------------------

Clone the latest Snaptron server code: ::
        git clone https://github.com/ChristopherWilks/snaptron.git

Python2.7, Tabix >= 1.2.1, and Sqlite3 >= 3.11.0 need to be compiled and already in the PATH before running the following.

From within the cloned snaptron directory run the following to install and setup a compilation (the following takes minutes->hours depending on amount of data): ::

        deploy/deploy_snaptron_generic.sh name_of_compilation /path/to/junctions.ts.gz /path/to/Bowtie/genome/index /path/to/annotation.gtfs/ new_source_id /path/to/sample/metadata.tsv
example: ::

        ./deploy/deploy_snaptron_generic.sh supermouse ./junctions.tsv.gz /data3/indexes/mm10/genome ./annotations 6 ./samples.tsv 

Common Pitfalls
---------------

The hardest dependency to get installed typically is PyLucene.
This is due to it's requirement of Java and the interface between Java and Python.
For this it's helpful if you have sudo/root on the machine you're trying to install to, though it's not required.
