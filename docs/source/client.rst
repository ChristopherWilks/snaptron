.. Snaptron documentation Client file

.. |date| date::
.. |time| date:: %H:%M

Generated on |date| at |time|.

=========================
Snaptron Client Interface
=========================

UPDATE: as of 2017-11-01 summarized raw gene expression counts can be 
queried from Snaptron using the same query/output format as the junctions.

Simply switch the endpoint from ``snaptron`` to ``genes`` in the Snaptron URL, e.g.: ::

        curl "http://snaptron.cs.jhu.edu/srav2/genes?regions=chr6:1-10714015&rfilter=samples_count>:10

Summarized raw gene expression counts are from recount:
https://jhubiostatistics.shinyapps.io/recount/


Snaptron Client Quickstart
--------------------------

NOTE: all counts are raw counts unless otherwise specified.
Please see the Normalization section for more information.

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


Normalization
-------------

The Snaptron WSI results will always return raw counts for sample coverages.

However, the Snaptron client will return normalized counts per sample if
``--normalize recount`` or ``--normalize jxcov`` is passed to it.

In the first case normalization is done by the recount method.
Every raw count is divided by the area-under-coverage (AUC) of the sample 
and then multiplied by a 40M 100bp reads scaling factor.
This is an appropriate method for either gene or junction results.

In the second case, normalization is done by dividing
every raw count by the total sum of junction coverage for the sample
and then multiplying by the average total sum of junction coverage 
across the SRAv2 samples (avg. of 3953678 across 43332 samples).
This method is only appropriate for junction results.

In both cases, normalization includes rounding following
the IEC 60559 approach for handling "5"s (go to nearest even digit).
This is to stay compatible with recount's normalization.

Any samples which, after normalization, have 0 count,
are removed before output and sample summary statistics per row
are recomputed on the remaining, normalized counts.

IMPORTANT NOTE: In any of the above cases, the sample
statistic-related query constraints (e.g. samples_count > 10)
are always computed on the raw counts, in both the client
and the WSI.  If normalization is requested in the Snaptron client,
the constraints are applied before normalization is performed.
This is due to normalization being currently implemented on the client side, 
rather than the server.
This may change in the future.
