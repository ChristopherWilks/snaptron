.. Snaptron documentation reference tables file

.. |date| date::
.. |time| date:: %H:%M

Generated on |date| at |time|.

=========================
Snaptron Reference Tables
=========================

Table 1. Query Types
--------------------
=============== ================================================================ ============ =============================================== ==================
Query Type      Description                                                      Multiplicity Format                                          Example
--------------- ---------------------------------------------------------------- ------------ ----------------------------------------------- ------------------
Region          chromosome based coordinates range (1-based); HUGO gene name     1            chr(1-22,X,Y,M):1-size of chromosome; gene_name chr21:1-500; CD99
Filter          range over summary statistic column values                       1 or more    column_name(>:,<:,:)number (integer or float)   coverage_avg>:10
Sample Metadata keyword and numeric range search over sample metadata            1 or more    fieldname(>:,<:,:)keyword                       description:cortex; SMRIN>:8
Sample IDs      limits results to only junctions found in specified samples IDs  1            sids=\\d+[,\\d+]*                               sids=2,40,50,100
Sample Group*   limits to only junctions found in specified sample group         1            sids=groupname                                  sids=Brain (gtex)
Snaptron IDs    one or more snaptron_ids                                         1            ids=\\d+[,\\d+]*                                ids=5,7,8
Sample IDs      one or more sample_ids                                           1            ids=\\d+[,\\d+]*                                ids=20,40,100
=============== ================================================================ ============ =============================================== ==================

\* The ``sids=groupname`` parameter is based on predefined groups of sample IDs.  These group definitions are found in the data directory of the compilation being queried, typically in a file ``samples.groups.tsv``, e.g. for GTEx: http://snaptron.cs.jhu.edu/data/gtex/samples.groups.tsv

The ``Region`` query type is required to be present if the ``Filter``, ``Sample Metadata``, ``Sample Group``, and/or ``Sample IDs`` types are used.

Table 2.  List of Snaptron Parameters
-------------------------------------
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter | WSI Endpoints           | Values                               | # Occurrences                                                             | Example                                                     | Description                                                                                                                                                    |
+===========+=========================+======================================+===========================================================================+=============================================================+================================================================================================================================================================+
| regions   | snaptron;genes          | chr[1-22XYM]:\\d+-\\d+;HUGO gene     | 1 but can take multiple arguments separated by a comma representing an OR | chr1:1-5000;DRD4                                            | coordinate intervals and/or HUGO gene names                                                                                                                    |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| sids      | snaptron;genes          | sids=(\\d+[,\\d+]*)|(groupname)      | 1                                                                         | sids=30,100,150 ; sids=Brain                                | filter to only junctions from >=1 samples in this list; uses the samples' rail_ids, can also take a predefined sample group name (e.g. GTEx tissue)            |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ids*      | snaptron;genes;samples  | ids=\\d+[,\\d+]*                     | 1                                                                         | ids=5,6,7                                                   | ID filter for snaptron_id (endpoint=snaptron) and rail_id (endpoint=samples); this only returns the specific records with those IDs                            |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| rfilter   | snaptron;genes          | fieldname[><!:]value                 | 0 or more                                                                 | rfilter=samples_count>:5&rfilter=coverage_sum:3             | point range filter (inclusion)                                                                                                                                 |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| sfilter   | snaptron;genes;samples  | fieldname:value OR freetext          | 0 or more                                                                 | sfilter=description:Cortex&sfilter=library_strategy:RNA-Seq | sample metadata filter (inclusion)                                                                                                                             |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| contains  | snaptron;genes          | 0,1                                  | 0-1 occurrences                                                           | contains=1                                                  | return only those junctions whose start and end coordinates are within the boundaries of the region (using either coordinates directly or passed in gene name) |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| exact     | snaptron;genes          | 0,1                                  | 0-1 occurrences                                                           | exact=1                                                     | return only those junctions whose start and end coordinates are match the boundaries of the region requested                                                   |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| either    | snaptron;genes          | 0,1,2                                | 0-1 occurrences                                                           | either=2                                                    | return only those junctions whose start (either=1) or end (either=2) coordinate match or are within the boundaries of the region requested                     |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| header    | snaptron;genes          | 0,1                                  | 0-1 occurrences                                                           | header=0                                                    | include the header as the first line (or not)                                                                                                                  |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| fields**  | snaptron;genes          | fields=fieldname[,fieldname]*        | 0 or more unique fieldnames within one fields clause                      | fields=snaptron_id,samples_count                            | which fields to return                                                                                                                                         |
+-----------+-------------------------+--------------------------------------+---------------------------------------------------------------------------+-------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

\* The ``ids`` parameter cannot be used with other parameters.

\*\*can include non-return field options such as: ``rc`` (result count)


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
| annotated*        | 0 or 1          | annotated:1          | whether both left and right splice sites in one or more annotations (default is both)     |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| left_annotated*   | 0 or 1          | left_annotated:1     | whether the left splice site is in one or more annotations                                |
+-------------------+-----------------+----------------------+-------------------------------------------------------------------------------------------+
| right_annotated*  | 0 or 1          | right_annotated:1    | whether the right splice site is in one or more annotations                               |
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

\* these fields are treated as booleans for the purpose of searching but as Strings when returned since if they are not 0, they will be a list of one or more annotation source abbreviations.  Also, importantly, if each splice site of a junction (left/right) is annotated separately (not connected), ``annotated`` will be 0 but BOTH the left and right annotated fields will not be 0.


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
| 8           | Yes      | annotated         | String                                          | If both ends of the intron are annotated as a splice site in some annotation                                            |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 9           | No       | left_motif        | String                                          | Splice site sequence bases at the left end of the intron                                                                |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 10          | No       | right_motif       | String                                          | Splice site sequence bases at the right end of the intron                                                               |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 11          | Yes      | left_annotated    | String                                          | If the left end splice site is annotated or not and which annotations it appears in (maybe more than once)              |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| 12          | Yes      | right_annotated   | String                                          | If the right end splice site is in an annotated or not, same as left_annotated                                          |
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
| 18          | No       | source_dataset_id | Integer                                         | Snaptron ID for the compilation. GTEx=1, SRAv2=2, TCGA=4)                                                               |
+-------------+----------+-------------------+-------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+

\* this field always starts with a ``,``; this is due to how it is searched when samples are used to filter a junction query (R+M or R+F+M).
The format of this field is a comma-delimited list of samples and their raw read coverage in that sample.
It uses the rail_id of the sample: ``,rail_id1:coverage1,rail_id2:coverage2,...``.
This rail_id matches the first column in the relevant compilation's ``samples.tsv`` file available
from the links previously listed in the ``Raw Data and Indices`` section.
