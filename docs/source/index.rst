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

As an example of a downstream interface that can be built on top of the Snaptron web service interface there is the SnaptronUI for which there are two instances, one for SRAv1 (~21,000 samples) and a second for SRAv2 (~49,000 samples):

SRAv1:
  http://stingray.cs.jhu.edu:8100

SRAv2
  http://stingray.cs.jhu.edu:8443

Caveat emptor, these instances are provided as examples only, at this time.  While they serve real data and may prove useful for investigations, they are not guaranteed to be stable/performant in anyway.

Quickstart
----------

First, we will present an example query and then break it down to allow the impatient users to get on with their research and skip the longer explanation of the details: ::

  curl "http://stingray.cs.jhu.edu:8090/srav1/snaptron?regions=chr6:1-514015&rfilter=samples_count:100"

The above command uses cURL to query the Snaptron web service for all junctions that overlap the coordinate range of ``1-514015`` on chromosome 6 and that have 1 or more reads coverage in exactly 100 samples (for CGI parsing reasons the .:. is used instead of .=. as a range operator).  The return format is a TAB delimited text stream of junction records, one per line including a header as the first line to explain the columns returned.

Gene symbols (exact HGNC gene symbols) can also be used instead of chromosome coordinates: ::

  curl "http://stingray.cs.jhu.edu:8090/srav1/snaptron?regions=CD99&rfilter=samples_count:20"

A Snaptron query is a set of predicates logically AND'ed together from three different query types, each with their own format. Table 1 displays the four different query types.  The three main query types are: region, range over a summary statistics column (.range.), a freetext/field search of the associated sample metadata (.metadata.), and an exact ID retrieval for both exon-exon junctions (Snaptron assigned IDs) and samples (Intropolis-assigned IDs).

A snaptron query may contain only one of the three types of queries or may contain all three, or some combination of two types.  In the example above the region and range query types are present as ``chr6:1-514015`` for the region type and ``samples_count:100`` for the range type.

There are currently (8/25/2016) two different Snaptron instances:

- SRAv1: ~42 million junctions from ~21 thousand public samples from the Sequence Read Archive using HG19 reference:
http://stingray.cs.jhu.edu:8090/srav1/snaptron

- SRAv2: ~81 million junctions from ~49 thousand public samples from the Sequence Read Archive using HG38 reference:
http://stingray.cs.jhu.edu:8090/srav2/snaptron


Table 1. Query Types
--------------------
=============== ================================================================ ============ =============================================== ==================
Query Type      Description                                                      Multiplicity Format                                          Example
--------------- ---------------------------------------------------------------- ------------ ----------------------------------------------- ------------------
Region          chromosome based coordinates range (1-based); HUGO gene name     1            chr(1-22,X,Y,M):1-size of chromosome; gene_name chr21:1-500; CD99
Range           range over summary statistic column values                       1 or more    column_name(>:,<:,:)number (integer or float)   coverage_avg>:10
Sample Metadata is-equal-to/contains text (keywords) search over sample metadata 1 or more    fieldname:keyword                               description:cortex
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
| ids       | snaptron; samples | ids=\d+[,\d+]*                       | 1                                                                         | ids=5,6,7                                                   | ID filter for snaptron_id (endpoint="snaptron") and sample_id (endpoint="samples")                                                                             |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| rfilter   | snaptron          | fieldname[><!:]value                 | 0 or more                                                                 | rfilter=samples_count>:5&rfilter=coverage_sum:3             | point range filter (inclusion)                                                                                                                                 |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| sfilter   | snaptron; samples | fieldname:value OR freetext          | 0 or more                                                                 | sfilter=description:Cortex&sfilter=library_strategy:RNA-Seq | sample metadata filter (inclusion)                                                                                                                             |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| contains  | snaptron          | 0,1                                  | 0-1 occurrences                                                           | contains=1                                                  | return only those junctions whose start and end coordinates are within the boundaries of the region (using either coordinates directly or passed in gene name) |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| exact     | snaptron          | 0,1                                  | 0-1 occurrences                                                           | exact=1                                                     | return only those junctions whose start and end coordinates are match the boundaries of the region requested                                                   |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| within    | snaptron          | 0,1,2                                | 0-1 occurrences                                                           | within=2                                                    | return only those junctions whose start (within=1) or end (within=2) coordinate match or are within the boundaries of the region requested                     |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| header    | snaptron          | 0,1                                  | 0-1 occurrences                                                           | header=0                                                    | include the header as the first line (or not)                                                                                                                  |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| fields**  | snaptron          | fields=fieldname[,fieldname]*        | 0 or more unique fieldnames within one fields clause                      | fields=snaptron_id,samples_count                            | which fields to return                                                                                                                                         |
+-----------+-------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

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

Often the Range query type columns (Table 4) can be used as a way to reduce the number of false positive junctions.  This can be done easily with the two columns: samples_count and coverage_sum.  Some suggested values from our own research are presented in Table 5.

Table 4. Range Query Fields ("rfilter" parameter)
-------------------------------------------------
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| Field             | Range of Values | Example              | Description                                                                               |
+===================+=================+======================+===========================================================================================+
| length            | 1-600K          | intron_length<:5000  | length of exon-exon junction (intron)                                                     |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| annotated         | 0 or 1          | annotated:1          | whether both left and right splice sites in one or more annotations                       |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| samples_count     | 1-Inf           | samples_count>:5     | number of samples in which this junction has one or more reads covering it                |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| coverage_sum**    | 1-Inf           | coverage_sum>:10     | aggregate count of reads covering the junction across all samples the junction appears in |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| coverage_avg**    | 1.0-Inf         | coverage_avg>:5.0    | average of read coverage across all samples the junction appears in                       |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| coverage_median** | 1.0-Inf         | coverage_median>:6.0 | median of read coverage across all samples the junction appears in                        |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+

\*\*for the GTEx dataset append a "2" to the end of this column to get query off the 2nd pass alignment read coverage statistics

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
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| Field Index | Field Name              | Type                                 | Description                                                                                                   | Example                |
+=============+=========================+======================================+===============================================================================================================+========================+
| 1           | DataSource:Type         | Abbrev:Single Character              | Differentiates between a return line of type Intron (I), Sample (S), or Gene (G).                             | SRAv1:I                |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 2*          | snaptron_id             | Integer                              | stable, unique ID for Snaptron junctions                                                                      | 5                      |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 3           | chromosome              | String                               | Reference ID for genomics coordinates                                                                         | chr7                   |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 4           | start                   | Integer                              | beginning (left) coordinate of intron                                                                         | 10113                  |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 5           | end                     | Integer                              | last (right) coordinate of intron                                                                             | 10244                  |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 6           | length                  | Integer                              | Length of intron coordinate span                                                                              | 132                    |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 7           | strand                  | Single Character                     | Orientation of intron (Watson or Crick)                                                                       | + or "-"               |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 8**         | annotated               | Boolean Integer                      | If both ends of the intron are annotated as *a* splice site in some annotation                                | 1 or 0                 |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 9           | left_motif              | String                               | Splice site sequence bases at the left end of the intron                                                      | GT                     |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 10          | right_motif             | String                               | Splice site sequence bases at the right end of the intron                                                     | AG                     |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 11**        | left_annotated          | String                               | If the left end splice site is annotated or not and which annotations it appears in (maybe more than once)    | aC19,cG19,cG38:1;0     |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 12**        | right_annotated         | String                               | If the right end splice site is in an annotated or not, same as left_annotated                                | aC19,cG19,cG38:1;0     |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 13          | samples                 | Comma separated list of Integers IDs | The list of samples which had one or more reads covering the intron(?). IDs are from the IntropolisDB.        | 5,10,14                |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 14          | read_coverage_by_sample | Comma separated list of Integers     | Coverage of the intron per sample (matches "samples" column position)                                         | 1,6,20                 |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 17*         | coverage_avg            | Float                                | Average coverage across all samples which had at least 1 read covering the intron in the first pass alignment | 8.667                  |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 18*         | coverage_median         | Float                                | Median coverage across all samples which had at least 1 read covering the intron in the first pass alignment  | 6                      |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+
| 19          | source_dataset_id       | Integer                              | Snaptron ID for the original dataset used (SRA, GTEx, TCGA)                                                   | SRAv1=0,SRAv2=1,GTEx=2 |
+-------------+-------------------------+--------------------------------------+---------------------------------------------------------------------------------------------------------------+------------------------+

\*\*These fields are not present in the GTEx version of the Snaptron webservice at this time.  They are not queryable in the SRA version.


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

