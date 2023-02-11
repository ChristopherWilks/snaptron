.. Snaptron documentation Data file

.. |date| date::
.. |time| date:: %H:%M

Generated on |date| at |time|.

=====================================
Snaptron Compilations and Source Data
=====================================

Snaptron Compilations (instances)
---------------------------------

Each compilation is either human (hg38 coordinates) or mouse (mm10 coordinates).  All compilations are human unless otherwise noted.

recount3 based Snaptron compilations include reprocessed existing TCGA samples and include additional samples from GTEx (v8) beyond those originally included in the recount2 based Snaptron compilations.  Also, the srav3h compilation was greatly expanded in recount3 to include many more studies while still covering many/most of the studies present in the recount2 version (srav2). We use "sample" and "SRA run" interchangeably here.

The following is a sample of potentially useful Snaptron instances (as of 2023-02-11), indexing different data sources (modify the example URL for your own queries).  You can use "curl -L <Snaptron_URL>" as a quick way to access results at the command line or paste the URL into a web browser:

- gtexv2: ~33 million junctions from ~19 thousand public samples from the GTEx project (recount3 version):
        http://snaptron.cs.jhu.edu/gtexv2/snaptron?regions=KCNIP4

- srav3h: ~228 million junctions from ~316 thousand public human samples from the Sequence Read Archive (recount3 version):
        http://snaptron.cs.jhu.edu/srav3h/snaptron?regions=ABCD3

- srav1m: ~148 million junctions from ~417 thousand public mouse samples from the Sequence Read Archive (recount3 version):
        http://snaptron.cs.jhu.edu/srav1m/snaptron?regions=ABCD3

- tcgav2: ~32 million junctions from ~11 thousand public samples from the TCGA project (recount3 version):
        http://snaptron.cs.jhu.edu/tcgav2/snaptron?regions=BRCA1

- tcga: ~36 million junctions from ~11 thousand public samples from the TCGA project (recount2 version):
        http://snaptron.cs.jhu.edu/tcga/snaptron?regions=BRCA1

- gtex: ~30 million junctions from ~10 thousand public samples from the GTEx project (recount2 version):
        http://snaptron.cs.jhu.edu/gtex/snaptron?regions=KCNIP4

- srav2: ~81 million junctions from ~49 thousand public samples from the Sequence Read Archive (recount2 version):
        http://snaptron.cs.jhu.edu/srav2/snaptron?regions=ABCD3


Compilation Registry
--------------------

You can query the current list of all active Snaptron compilations being publicly hosted by the Langmead lab:
http://snaptron.cs.jhu.edu/snaptron/registry

That returns a JSON structure where the top level keys are the compilation names and the nested dictionaries per compilation are the list of metadata fields available for that compilation and their types ("t"=text/strings, "i"=integer,"f"=floating) from the Lucene indexes for each compilation.

Raw Data and Indices
--------------------

All data and the associated indices backing Snaptron are available here (by compilation):
http://snaptron.cs.jhu.edu/data/
