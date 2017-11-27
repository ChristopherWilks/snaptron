.. Snaptron documentation metadata file

.. |date| date::
.. |time| date:: %H:%M

Generated on |date| at |time|.

========================
Snaptron Sample Metadata
========================

Each of the above compilations has its own set of sample metadata with varying field names and definitions.
Snaptron indexes these metadata fields in a document store (Lucene) for full text retrieval.
Numeric columns (e.g. RIN in the GTEx compilation) are indexed to support range based lookups.

Query metadata and sample metadata text is converted to lower case before indexing/querying to make searches case-insensitive.


Both sample-only searches and junction searches limited by a sample predicate can be performed: ::

  curl "http://snaptron.cs.jhu.edu/gtex/samples?sfilter=SMRIN>8"

will return a list of samples which have a RIN value > 8. ::

  curl "http://snaptron.cs.jhu.edu/srav2/snaptron?regions=chr6:1-10714015&rfilter=samples_count>:10&sfilter=description:cortex"

will return a list of junctions and their list of summary stats calcuated from the intersection of the region and rfilter
predicates and which contain at least one sample in the list of samples which have "cortex" in their description field.

Further, you can also query by sample ID to simply return all the metadata for the submitted set of sample IDs: ::

  curl "http://snaptron.cs.jhu.edu/srav2/samples?ids=0,2,500"


Sample Metadata Fields
----------------------

A complete list of all sample metadata fields and types stored and indexed by Snaptron are available for each compilation:

- TCGA
http://snaptron.cs.jhu.edu/data/tcga/samples.fields.tsv

- GTEx
http://snaptron.cs.jhu.edu/data/gtex/samples.fields.tsv

- SRAv2
http://snaptron.cs.jhu.edu/data/srav2/samples.fields.tsv

- SRAv1
http://snaptron.cs.jhu.edu/data/srav1/samples.fields.tsv


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
