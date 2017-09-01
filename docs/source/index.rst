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

The published Snaptron paper is here:

https://doi.org/10.1093/bioinformatics/btx547

.. toctree::
   :maxdepth: 2

Questions can be asked in the project's Gitter channel_.

.. _channel: https://gitter.im/snaptron/Lobby


Snaptron Client Quickstart
--------------------------

https://github.com/ChristopherWilks/snaptron-experiments

The Snaptron command-line client is a lightweight Python
interface for querying the Snaptron web services which are documented in detail below.

To run the client (assuming Python is in the path): ::

        git clone https://github.com/ChristopherWilks/snaptron-experiments.git
        cd snaptron-experiments
        ./qs

The following are examples of using the Snaptron client, some of which are from the Snaptron preprint.
The default data compilation is SRAv2 (~50K samples, ~81M junctions).

To get all splice junctions which fall fully within the BRCA1 gene extent with a sample count of at least 100 which are
included in at least one annotation (both splice sites): ::

        ./qs --region "BRCA1" --contains 1 --filters "samples_count>=100&annotated=1"

If instead you have a coordinate-defined region rather than a gene, you could do the following to look for junctions which overlap the region and are potentially novel but also have significant sample and read support: ::
        
        ./qs --region "chr2:29446395-30142858" --filters "samples_count>=100&coverage_sum>=150"

You can further limit queries by searching for keywords in the sample-associated metadata.
The following query returns all junctions which overlap the region of the KMT2E gene which occur in at least 5 samples which also contain the keyword "cortex" in their description field: ::
        
        ./qs --region "KMT2E" --filters "samples_count>=5" --metadata "description:cortex"

This query will return all junctions (no filtering) that overlap the gene TP53 from the TCGA (cancer-related) data compilation: ::
        
        ./qs --region "TP53" --datasrc tcga

The following will return all sample metadata for those samples which contain the keyword "brain" in their description field ranked by a TF-IDF score determining that sample's relevance to the query: ::

        ./qs --metadata "description:brain"

The analyses from the Snaptron preprint can be recreated as a whole with the following command: ::

        ./run_all.sh

Individual commands from the Snaptron preprint are as follows (except SSC due to its length).
These are also documented in the scripts/ directory of the snaptron-experiments repository.

1) Tissue specificity (TS) for repetitive element loci (REL) junctions analysis (assumes Rscript is in the path): ::
        
        ./qs --query-file ./data/rel_splices.hg38.snap.tsv --function ts --datasrc gtex | tee ./rel_ts_list.tsv | Rscript ./scripts/tissue_specificty_testing.R

2) Junction inclusion ratio (JIR) with additional filtering for total coverage: ::

        ./qs --query-file data/alk_alt_tss.hg19.snap.tsv --function jir --datasrc srav1 | perl -ne 'chomp; $s=$_; if($s=~/jir_score/) { print "$s\n"; next}; @f=split(/\t/,$_); next if($f[1]+$f[2] < 50); print "".join("\t",@f)."\n";' > alk_alt_tss.hg19.srav1.jir_results.tsv


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

Raw Data and Indices
--------------------

All data and the associated indices backing Snaptron are available here (by compilation):
http://snaptron.cs.jhu.edu/data/

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

Further, you can also query by sample ID to simply return all the metadata for the submitted set of sample IDs: ::

  curl "http://snaptron.cs.jhu.edu/srav2/samples?ids=0,2,500"


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

-------------------
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
| ids*      | snaptron; samples | ids=\d+[,\d+]*                       | 1                                                                         | ids=5,6,7                                                   | ID filter for snaptron_id (endpoint=snaptron) and sample_id (endpoint=samples)                                                                                 |
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

\* The ``ids`` parameter cannot be used with other parameters.

\*\*can include non-return field options such as: ``rc`` (result count)

Individual records for junctions can be accessed via the Snaptron ID directly as: ::
        
        curl "http://snaptron.cs.jhu.edu/srav1/snaptron/5"

and for a sample record through its Rail ID: ::

        curl "http://snaptron.cs.jhu.edu/srav1/samples/10"


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

.. Table 5.  Suggested Quality Threshold for Selected Range Columns
.. ----------------------------------------------------------------
.. ==============  ======================  ===================
.. Selected Field  Quality Threshold Type  Threshold Predicate
.. --------------  ----------------------  -------------------
.. samples_count   baseline                >:5
.. samples_count   higher confidence       >:1000
.. coverage_sum    baseline                >:10?
.. coverage_sum    higher confidence       >:50?
.. intron_length   baseline                <:10000?
.. intron_length   higher confidence       <:3000?
.. ==============  ======================  ===================

The return format is a TAB-delimited series of fields where each line represents a unique intron call.  Table 5 displays the complete list of fields in the return format of the Snaptron web service.  The ``chromosome``, ``start``, and, ``end`` fields are a special case where the index is a combination of all three of them together.

Table 5. Complete list of Snaptron Fields In Return Format
----------------------------------------------------------
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Field Index | Indexed? | Field Name        | Type                                            | Description                                                                                                             |
+=============+==========+===================+=================================================+=========================================================================================================================+
| 1           | No       | DataSource:Type   | Abbrev:Single Character                         | Differentiates between a return line of type Intron (I), Sample (S), or Gene (G).                                       |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 2           | Yes      | snaptron_id       | Integer                                         | stable, unique ID for Snaptron junctions                                                                                |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 3           | Yes      | chromosome        | String                                          | Reference ID for genomics coordinates                                                                                   |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 4           | Yes      | start             | Integer                                         | beginning (left) coordinate of intron                                                                                   |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 5           | Yes      | end               | Integer                                         | last (right) coordinate of intron                                                                                       |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 6           | Yes      | length            | Integer                                         | Length of intron coordinate span                                                                                        |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 7           | Yes      | strand            | Single Character                                | Orientation of intron (Watson or Crick)                                                                                 |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 8           | Yes      | annotated         | Boolean Integer                                 | If both ends of the intron are annotated as a splice site in some annotation                                            |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 9           | No       | left_motif        | String                                          | Splice site sequence bases at the left end of the intron                                                                |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 10          | No       | right_motif       | String                                          | Splice site sequence bases at the right end of the intron                                                               |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 11          | No       | left_annotated    | String                                          | If the left end splice site is annotated or not and which annotations it appears in (maybe more than once)              |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 12          | No       | right_annotated   | String                                          | If the right end splice site is in an annotated or not, same as left_annotated                                          |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 13          | No       | samples*          | Comma separated list of tuples: integer:integer | The list of samples which had one or more reads covering the intron and their coverages. IDs are from the IntropolisDB. |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 14          | Yes      | samples_count     | Integer                                         | Total number of samples that have one or more reads covering this junction                                              |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 15          | Yes      | coverage_sum      | Integer                                         | Sum of all samples coverage for this junction                                                                           |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 16          | Yes      | coverage_avg      | Float                                           | Average coverage across all samples which had at least 1 read covering the intron in the first pass alignment           |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 17          | Yes      | coverage_median   | Float                                           | Median coverage across all samples which had at least 1 read covering the intron in the first pass alignment            |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 18          | No       | source_dataset_id | Integer                                         | Snaptron ID for the original dataset used (SRA, GTEx, TCGA)                                                             |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+

\* this field always starts with a ``,``; this is due to how it is searched when samples are used to filter a junction query (R+M or R+F+M)

Mock Graphical User Interface
-----------------------------

As a limited example of a downstream interface that can be built on top of the Snaptron web service interface there is the Snaptron GUI for which there are several instances for various datasets:

TCGA (~11K samples, ~36M junctions):
  http://snaptron.cs.jhu.edu:8090

GTEx (~10K samples, ~30M junctions):
  http://snaptron.cs.jhu.edu:8000

SRAv2 (~50K samples, ~81M junctions):
  http://snaptron.cs.jhu.edu:8443

SRAv1 (~21K samples, ~42M junctions):
  http://snaptron.cs.jhu.edu:8100

Caveat emptor, these instances are provided as examples only for the time being.  While they serve real data and may prove useful for investigations, they are not guaranteed to be stable/performant in any way.

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

