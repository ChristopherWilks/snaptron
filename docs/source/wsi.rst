.. Snaptron documentation WSI file

.. |date| date::
.. |time| date:: %H:%M

Generated on |date| at |time|.

===============================
Snaptron Web Services Interface
===============================

RESTful Web Services Interface Quickstart
-----------------------------------------

First, we will present an example query and then break it down to allow the impatient users to get on with their research and skip the longer explanation of the details: ::

  curl "http://snaptron.cs.jhu.edu/srav2/snaptron?regions=chr6:1-514015&rfilter=samples_count:100"

The above command uses cURL to query the Snaptron web service for all junctions that overlap the coordinate range of ``1-514015`` on chromosome 6 and that have 1 or more reads coverage in exactly 100 samples (for CGI parsing reasons the .:. is used instead of .=. as a range operator).  The return format is a TAB delimited text stream of junction records, one per line including a header as the first line to explain the columns returned.

Gene symbols (exact HGNC gene symbols) can also be used instead of chromosome coordinates: ::

  curl "http://snaptron.cs.jhu.edu/srav2/snaptron?regions=CD99&rfilter=samples_count:20"

If the gene symbol maps to multiple genomic regions they will all be returned by the Snaptron web services rather than Snaptron attempting to decide which region is being requested.

A Snaptron query is a set of predicates logically AND'ed together from three different query types, each with their own format. Table 1 displays the four different query types.  The three main query types are: region, range over a summary statistics column (.range.), a freetext/field search of the associated sample metadata (.metadata.), and an exact ID retrieval for both exon-exon junctions (Snaptron assigned IDs) and samples (Intropolis-assigned IDs).

A snaptron query may contain only one of the three types of queries or may contain all three, or some combination of two types.  In one of the examples above the region and range query types are present as ``chr6:1-514015`` for the region type and ``samples_count:100`` for the range type.

WSI Forbidden Characters
------------------------

Because of how Snaptron parses queries the following characters are not allowed as part of search terms/phrases:

        ><:!


Example WSI Queries
-------------------

[Result counts below include header(s)]

Results: 46; Time: 0m1.179s: ::

  curl "http://snaptron.cs.jhu.edu/srav2/snaptron?regions=BRCA1&rfilter=samples_count>:100&rfilter=annotated:1"


Results: 40; Time: 0m0.736s: ::

  curl "http://snaptron.cs.jhu.edu/srav2/snaptron?regions=chr2:29446395-30142858&rfilter=samples_count>:100&rfilter=coverage_sum>:150"

Results: 27; Time: 0m1.129s: ::

  curl "http://snaptron.cs.jhu.edu/srav2/snaptron?regions=KMT2E&rfilter=samples_count>:5&sfilter=description:cortex"

.. Add list of sample metadata columns for each compilation

Individual records for junctions can be accessed via the Snaptron ID directly as: ::
        
        curl "http://snaptron.cs.jhu.edu/srav2/snaptron/5"

and for a sample record through its Rail ID: ::

        curl "http://snaptron.cs.jhu.edu/srav2/samples/10"

In contrast, the ``sids`` filter can be used to constrain a query to return only junctions that have read coverage in the specified samples: ::

        curl "http://snaptron.cs.jhu.edu/srav2/snaptron?regions=ALK&sids=40099,40100"


Exact HUGO (HGNC) gene symbols can be searched in snaptron SRA instance in lieu of actual coordinates.   If the gene symbol had multiple coordinate ranges that were either on different chromosomes or more than 10,000 bases apart, Snaptron will do multiple tabix lookups and will stream them back in coordinate order per chromosome (the chromosome order itself is sorted via default python sorted which is not 1-22,X,Y,M).

The gene symbol to coordinate mapping is provided from the UCSC RefSeq .Flat. dataset: http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refFlat.txt.gz

That dataset maps HUGO (HGNC) gene symbols to RefSeq gene IDs and transcript coordinates.

Please see the `Reference Tables page <reftables.html>`_ for detailed information on supported fields in the WSI.
For more information about sample metadata please see the `Sample Metadata page <metadata.html>`_.
