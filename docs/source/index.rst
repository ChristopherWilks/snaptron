.. Snaptron documentation master file, created by
   sphinx-quickstart on Mon Apr 25 16:03:47 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. |date| date::
.. |time| date:: %H:%M

Generated on |date| at |time|.

===================
Snaptron User Guide
===================
Christopher Wilks, Phani Gaddipati, Abhinav Nellore, Ben Langmead

.. toctree::
   :maxdepth: 2

SnaptronUI
----------

As an example of a downstream interface that can be built on top of the Snaptron web service interface there is the SnaptronUI for which there are several instances for various datasets:

TCGA (~11K samples, ~36M junctions):
  http://snaptron.cs.jhu.edu:8090

GTEx (~10K samples, ~30M junctions):
  http://snaptron.cs.jhu.edu:8000

SRAv2 (~50K samples, ~81M junctions):
  http://snaptron.cs.jhu.edu:8443

SRAv1 (~21K samples, ~42M junctions):
  http://snaptron.cs.jhu.edu:8100

Caveat emptor, these instances are provided as examples only for the time being.  While they serve real data and may prove useful for investigations, they are not guaranteed to be stable/performant in any way.

RESTful WSI Quickstart
----------------------

First, we will present an example query and then break it down to allow the impatient users to get on with their research and skip the longer explanation of the details: ::

  curl "http://snaptron.cs.jhu.edu/srav1/snaptron?regions=chr6:1-514015&rfilter=samples_count:100"

The above command uses cURL to query the Snaptron web service for all junctions that overlap the coordinate range of ``1-514015`` on chromosome 6 and that have 1 or more reads coverage in exactly 100 samples (for CGI parsing reasons the .:. is used instead of .=. as a range operator).  The return format is a TAB delimited text stream of junction records, one per line including a header as the first line to explain the columns returned.

Gene symbols (exact HGNC gene symbols) can also be used instead of chromosome coordinates: ::

  curl "http://snaptron.cs.jhu.edu/srav1/snaptron?regions=CD99&rfilter=samples_count:20"

If the gene symbol maps to multiple genomic regions they will all be returned by the Snaptron web services rather than Snaptron attempting to decide which region is being requested.

A Snaptron query is a set of predicates logically AND'ed together from three different query types, each with their own format. Table 1 displays the four different query types.  The three main query types are: region, range over a summary statistics column (.range.), a freetext/field search of the associated sample metadata (.metadata.), and an exact ID retrieval for both exon-exon junctions (Snaptron assigned IDs) and samples (Intropolis-assigned IDs).

A snaptron query may contain only one of the three types of queries or may contain all three, or some combination of two types.  In the example above the region and range query types are present as ``chr6:1-514015`` for the region type and ``samples_count:100`` for the range type.

Snaptron Compilations (instances)
---------------------------------

There are currently (11/16/2016) four Snaptron instances indexing different data sources (modify the example URL for your own queries):

- TCGA: ~36 million junctions from ~11 thousand public samples from the TCGA consortium sequences using HG38 reference:
http://snaptron.cs.jhu.edu/tcga/snaptron?regions=BRCA1

- GTEx: ~30 million junctions from ~10 thousand public samples from the GTEx consortium sequences using HG38 reference:
http://snaptron.cs.jhu.edu/gtex/snaptron?regions=KCNIP4

- SRAv2: ~81 million junctions from ~49 thousand public samples from the Sequence Read Archive using HG38 reference:
http://snaptron.cs.jhu.edu/srav2/snaptron?regions=ABCD3

- SRAv1 (legacy, replaced by SRAv2): ~42 million junctions from ~21 thousand public samples from the Sequence Read Archive using HG19 reference:
http://snaptron.cs.jhu.edu/srav1/snaptron?regions=KMT2E

Forbidden Characters
--------------------

Because of how Snaptron parses queries the following characters are not allowed as part of search terms/phrases:

        ><:!

Sample Metadata
---------------

Each of the above compilations has its own set of sample metadata with varying field names and definitions.
Snaptron indexes these metadata fields in a document store (Lucene) for full text retrieval.
Numeric columns (e.g. RIN in the GTEx compilation) are indexed to support range based lookups.

Query metadata and sample metadata text is converted to lower case before indexing/querying to make searches case-insensitive.


Both sample-only searches and junction searches limited by a sample predicate can be performed: ::

  curl "http://snaptron.cs.jhu.edu/gtex/samples?sfilter=sfilter=SMRIN>8"

will return a list of samples which have a RIN value > 8. ::

  curl "http://snaptron.cs.jhu.edu/srav1/snaptron?regions=chr6:1-514015&rfilter=samples_count:100&sfilter=description:cortex"

will return a list of junctions and their list of summary stats calcuated from the intersection of the region and rfilter
predicates and which contain at least one sample in the list of samples which have "cortex" in their description field.

A complete list of all sample metadata fields and types stored and indexed by Snaptron are available for each compilation:

- TCGA
http://snaptron.cs.jhu.edu/data/tcga/samples.fields.tsv

- GTEx
http://snaptron.cs.jhu.edu/data/gtex/samples.fields.tsv

- SRAv2
http://snaptron.cs.jhu.edu/data/srav2/samples.fields.tsv

- SRAv1
http://snaptron.cs.jhu.edu/data/srav1/samples.fields.tsv


---------------------------
Sample Metadata Field Types
---------------------------

Lucene types are reported for each field in the above TSV files:

- ``text``
Input field tokenized into one or more terms by whitespace before indexing to support "contains" searching

Example:
a free-text description of the RNA-seq sequencing protocol

- ``string``
Input field indexed as one term (not tokenized)

Example:
controlled vocabulary field such as an NCBI sample accession

- ``integer``
Numeric input field indexed to support range searches

Example:
age at diagnosis for a cancer patient

- ``float``
Numeric input field indexed to support range searches, used if any floating point values were present in input

Example:
RNA-seq integrity value (RIN)

NOTE: Lucene stores the input field as a float, but range queries need to be specified as integers for now, even for float fields


If a metadata field for a particular sample is empty/NA or is a string and the field type is numeric, that particular entry is set to NULL in Lucene.

.. Add list of sample metadata columns for each compilation

Reference Tables
----------------

Table 1. Query Types
--------------------
=============== ================================================================ ============ =============================================== ==================
Query Type      Description                                                      Multiplicity Format                                          Example
--------------- ---------------------------------------------------------------- ------------ ----------------------------------------------- ------------------
Region          chromosome based coordinates range (1-based); HUGO gene name     1            chr(1-22,X,Y,M):1-size of chromosome; gene_name chr21:1-500; CD99
Filter          range over summary statistic column values                       1 or more    column_name(>:,<:,:)number (integer or float)   coverage_avg>:10
Sample Metadata keyword and numeric range search over sample metadata            1 or more    fieldname(>:,<:,:)keyword                       description:cortex; SMRIN>:8
Snaptron IDs    one or more snaptron_ids                                         1 or more    ids=\d+[,\d+]*                                  ids=5,7,8
Sample IDs      one or more sample_ids                                           1 or more    ids=\d+[,\d+]*                                  ids=20,40,100
=============== ================================================================ ============ =============================================== ==================

Table 2.  List of Snaptron Parameters
-------------------------------------
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | WSI Endpoints     | Values                               | # Occurrences                                                             | Example                                                     | Description                                                                                                                                                    |
+===========+===================+======================================+===========================================================================+=============================================================+================================================================================================================================================================+
| regions   | snaptron          | chr[1-22XYM]:\d+-\d+; HUGO gene name | 1 but can take multiple arguments separated by a comma representing an OR | chr1:1-5000;DRD4                                            | coordinate intervals and/or HUGO gene names                                                                                                                    |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ids*      | snaptron; samples | ids=\d+[,\d+]*                       | 1                                                                         | ids=5,6,7                                                   | ID filter for snaptron_id (endpoint="snaptron") and sample_id (endpoint="samples")                                                                             |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| rfilter   | snaptron          | fieldname[><!:]value                 | 0 or more                                                                 | rfilter=samples_count>:5&rfilter=coverage_sum:3             | point range filter (inclusion)                                                                                                                                 |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| sfilter   | snaptron; samples | fieldname:value OR freetext          | 0 or more                                                                 | sfilter=description:Cortex&sfilter=library_strategy:RNA-Seq | sample metadata filter (inclusion)                                                                                                                             |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| contains  | snaptron          | 0,1                                  | 0-1 occurrences                                                           | contains=1                                                  | return only those junctions whose start and end coordinates are within the boundaries of the region (using either coordinates directly or passed in gene name) |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| exact     | snaptron          | 0,1                                  | 0-1 occurrences                                                           | exact=1                                                     | return only those junctions whose start and end coordinates are match the boundaries of the region requested                                                   |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| either    | snaptron          | 0,1,2                                | 0-1 occurrences                                                           | either=2                                                    | return only those junctions whose start (either=1) or end (either=2) coordinate match or are within the boundaries of the region requested                     |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| header    | snaptron          | 0,1                                  | 0-1 occurrences                                                           | header=0                                                    | include the header as the first line (or not)                                                                                                                  |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| fields**  | snaptron          | fields=fieldname[,fieldname]*        | 0 or more unique fieldnames within one fields clause                      | fields=snaptron_id,samples_count                            | which fields to return                                                                                                                                         |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

\* individual records for junction record can be accessed via the Snaptron ID directly as: ::
        curl "http://snaptron.cs.jhu.edu/srav1/snaptron/5"
and for a sample record through its Rail ID: ::        
        curl "http://snaptron.cs.jhu.edu/srav1/samples/10"

\*\*can include non-return field options such as: “rc” (result count)


Tables 3 and 4 show the queryable fields for region and range query types respectively.
Fields from tables 3 and 4 can be mixed together in the same query though only one region predicate is allowed per query as specified in Table 1 above.

Table 3. Region Query Fields ("regions" parameter)
--------------------------------------------------
+--------------+--------------------------------------+------------+--------------------------+
| Field        | Range of Values                      | Example    | Description              |
+==============+======================================+============+==========================+
| coordinate*  | chr(1-22;X;Y;M):1-size of chromosome | chr1:4-100 | chromosome:start-end     |
+--------------+--------------------------------------+------------+--------------------------+
| gene symbol* | a-zA-Z0-9                            | CD99       | HUGO (HGNC) gene symbols |
+--------------+--------------------------------------+------------+--------------------------+

\*you can either pass a coordinate string or a gene symbol in the interval query segment, but not both

Often the query filter columns (Table 4) can be used as a way to reduce the number of false positive junctions.  This can be done easily with the two columns: samples_count and coverage_sum.  Some suggested values from our own research are presented in Table 5.

Table 4. Query Filter Fields ("rfilter" parameter)
--------------------------------------------------
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| Field             | Range of Values | Example              | Description                                                                               |
+===================+=================+======================+===========================================================================================+
| length            | 1-500K          | intron_length<:5000  | length of exon-exon junction (intron)                                                     |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| annotated         | 0 or 1          | annotated:1          | whether both left and right splice sites in one or more annotations (default is both)     |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| strand            | ``+`` or ``-``  | strand:+             | which strand to require (default is both)                                                 |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| samples_count     | 1-Inf           | samples_count>:5     | number of samples in which this junction has one or more reads covering it                |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| coverage_sum      | 1-Inf           | coverage_sum>:10     | aggregate count of reads covering the junction across all samples the junction appears in |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| coverage_avg      | 1.0-Inf         | coverage_avg>:5.0    | average of read coverage across all samples the junction appears in                       |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| coverage_median   | 1.0-Inf         | coverage_median>:6.0 | median of read coverage across all samples the junction appears in                        |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+

Exact HUGO (HGNC) gene symbols can be searched in snaptron SRA instance in lieu of actual coordinates.   If the gene symbol had multiple coordinate ranges that were either on different chromosomes or more than 10,000 bases apart, Snaptron will do multiple tabix lookups and will stream them back in coordinate order per chromosome (the chromosome order itself is sorted via default python sorted which is not 1-22,X,Y,M).

The gene symbol to coordinate mapping is provided from the UCSC RefSeq .Flat. dataset: http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refFlat.txt.gz

That dataset maps HUGO (HGNC) gene symbols to RefSeq gene IDs and transcript coordinates.

Table 5.  Suggested Quality Threshold for Selected Range Columns
----------------------------------------------------------------
==============  ======================  ===================
Selected Field  Quality Threshold Type  Threshold Predicate
--------------  ----------------------  -------------------
samples_count   baseline                >:5
samples_count   higher confidence       >:1000
coverage_sum    baseline                >:10?
coverage_sum    higher confidence       >:50?
intron_length   baseline                <:10000?
intron_length   higher confidence       <:3000?
==============  ======================  ===================

The return format is a TAB-delimited series of fields where each line represents a unique intron call.  Table 6 displays the complete list of fields in the return format of the Snaptron web service.  Fields marked with an "*" are queryable as they are specifically indexed.  The ``chromosome``, ``start``, and, ``end`` fields are a special case where the index is a combination of all three of them together.

Table 6. Complete list of Snaptron Fields In Return Format
----------------------------------------------------------
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| Field Index | Field Name        | Type                                            | Description                                                                                                             | Example                       |
+=============+===================+=================================================+=========================================================================================================================+===============================+
| 1           | DataSource:Type   | Abbrev:Single Character                         | Differentiates between a return line of type Intron (I), Sample (S), or Gene (G).                                       | SRAv1:I                       |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 2*          | snaptron_id       | Integer                                         | stable, unique ID for Snaptron junctions                                                                                | 5                             |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 3           | chromosome        | String                                          | Reference ID for genomics coordinates                                                                                   | chr7                          |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 4           | start             | Integer                                         | beginning (left) coordinate of intron                                                                                   | 10113                         |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 5           | end               | Integer                                         | last (right) coordinate of intron                                                                                       | 10244                         |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 6           | length            | Integer                                         | Length of intron coordinate span                                                                                        | 132                           |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 7           | strand            | Single Character                                | Orientation of intron (Watson or Crick)                                                                                 | ``+`` or ``-``                |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 8           | annotated         | Boolean Integer                                 | If both ends of the intron are annotated as a splice site in some annotation                                            | 1 or 0                        |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 9           | left_motif        | String                                          | Splice site sequence bases at the left end of the intron                                                                | GT                            |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 10          | right_motif       | String                                          | Splice site sequence bases at the right end of the intron                                                               | AG                            |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 11          | left_annotated    | String                                          | If the left end splice site is annotated or not and which annotations it appears in (maybe more than once)              | aC19,cG19,cG38:1;0            |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 12          | right_annotated   | String                                          | If the right end splice site is in an annotated or not, same as left_annotated                                          | aC19,cG19,cG38:1;0            |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 13          | samples*          | Comma separated list of tuples: integer:integer | The list of samples which had one or more reads covering the intron and their coverages. IDs are from the IntropolisDB. | ,5:10,10:2,14:3               |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 14          | samples_count     | Integer                                         | Total number of samples that have one or more reads covering this junction                                              | 20                            |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 15          | coverage_sum      | Integer                                         | Sum of all samples coverage for this junction                                                                           | 10                            |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 16          | coverage_avg      | Float                                           | Average coverage across all samples which had at least 1 read covering the intron in the first pass alignment           | 8.667                         |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 17          | coverage_median   | Float                                           | Median coverage across all samples which had at least 1 read covering the intron in the first pass alignment            | 6                             |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+
| 18          | source_dataset_id | Integer                                         | Snaptron ID for the original dataset used (SRA, GTEx, TCGA)                                                             | SRAv1=0,GTEx=1,SRAv2=2,TCGA=4 |
+-------------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+-------------------------------+

\* this field always starts with a ``,``; this is due to how it is searched when samples are used to filter a junction query (R+M or R+F+M)

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

