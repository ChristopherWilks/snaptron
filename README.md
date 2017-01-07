# snaptron
fast webservices based query tool for searching exon-exon splice junctions and related sample metadata

User Guide:
http://snaptron.cs.jhu.edu

Deployment:

git clone git@github.com:ChristopherWilks/snaptron.git

NOTE: Avoid setting Snaptron up on a Lustre or NFS filesystem
since Snaptron's reliance on SQLite may cause problems on those systems.

To setup an instance based on a particular compilation (srav1, srav2, gtex, tcga):

> ./deploy_snaptron.sh srav1

To enable the uncompressed version of the Tabix indices, you must first download
our modified version of [HTSlib 1.2.1] (http://snaptron.cs.jhu.edu/data/htslib-1.2.1_nocomp.tar.gz)
source which sets the compression level to 0 (no compression).

You must build the source and make sure the resulting bgzip binary ahead of any
other bgzip versions in your PATH.

Then run the above script with an additional argument:

> ./deploy_snaptron.sh srav1 1
