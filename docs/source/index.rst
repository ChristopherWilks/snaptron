.. Snaptron documentation master file, created by
   sphinx-quickstart on Mon Apr 25 16:03:47 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===================
Snaptron User Guide
===================

.. toctree::
   :maxdepth: 2

Quickstart
----------

First, we will present an example query and then break it down to allow the impatient users to get on with their research and skip the longer explanation of the details: ::

  curl "http://stingray.cs.jhu.edu:8090/srav1/snaptron?region=chr6:1-514015&rfilter=samples_count:100"

The above command uses cURL to query the Snaptron web service for all junctions that overlap the coordinate range of 1-514015 on chromosome 6 and that have 1 or more reads coverage in exactly 100 samples (for CGI parsing reasons the .:. is used instead of .=. as a range operator).  The return format is a TAB delimited text stream of junction records, one per line including a header as the first line to explain the columns returned.

Gene symbols (exact HUGO gene symbols) can also be used instead of chromosome coordinates: ::

  curl "http://stingray.cs.jhu.edu:8090/srav1/snaptron?regions=CD99&rfilter=samples_count:20"

A Snaptron query is a set of predicates logically AND.ed together from three different query types, each with their own format. Table 1 displays the four different query types.  The three main query types are: region, range over a summary statistics column (.range.), a freetext/field search of the associated sample metadata (.metadata.), and an exact ID retrieval for both exon-exon junctions (Snaptron assigned IDs) and samples (Intropolis-assigned IDs).

A snaptron query may contain only one of the three types of queries or may contain all three, or some combination of two types.  In the example above the region and range query types are present as chr6:1-514015 for the region type and samples_count:100 for the range type.

Table 1. Query Types

=============== ================================================================ ============ =============================================== ==================
Query Type      Description                                                      Multiplicity Format                                          Example
--------------- ---------------------------------------------------------------- ------------ ----------------------------------------------- ------------------
Region          chromosome based coordinates range (1-based); HUGO gene name     0-1          chr(1-22,X,Y,M):1-size of chromosome; gene_name chr21:1-500; CD99
Range           range over summary statistic column values                       0 or more    column_name(>:,<:,:)number (integer or float)   coverage_avg>:10
Sample Metadata is-equal-to/contains text (keywords) search over sample metadata 0 or more    fieldname:keyword                               description:cortex
Snaptron IDs    one or more snaptron_ids                                         0 or more    snaptron_id=\d+[,\d+]*                          snaptron_id=5,7,8
=============== ================================================================ ============ =============================================== ==================

Table 2 shows the queryable fields and their query type.  Often the Range query type columns will be used as a way to reduce the number of false positive junctions.  This can be done easily with the two columns: samples_count and coverage_sum.  For example some suggested values from our own research are presented in Table 3.

Table 2. Query Fields


================================== ======================= =========================================================== =======================
Field                              Query Type              Range of Values                                             Example
---------------------------------- ----------------------- ----------------------------------------------------------- -----------------------
coordinate* (chromosome:start-end) Interval                chr(1-22,X,Y,M):1-size of chromosome                        chr1:4-100
gene symbol*                       string exact match      HUGO gene symbols                                           CD99
length                             Range                   1-600K                                                      intron_length<:5000
samples_count                      Range                   1-Inf                                                       samples_count>:5  
coverage_sum**                     Range                   1-Inf                                                       coverage_sum>:10
coverage_avg**                     Range                   1.0-Inf                                                     coverage_avg>:5.0
coverage_median**                  Range                   1.0-Inf                                                     coverage_median>:6.0
snaptron_id                        Set                     unique, stable snaptron specific IDs, one per intron record snaptron_id=5
================================== ======================= =========================================================== =======================

[TODO: add sample metadata fields]











* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

