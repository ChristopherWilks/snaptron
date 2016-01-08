#!/usr/bin/env python
"""
process_introns.py
Abhi Nellore
10/2/2015
modified by Chris Wilks
to just annotate intron splice sites (no sequence)
and include the length of the intron

Also says whether intron splice sites are in
annotation. Requires extract_splice_sites.py from HISAT v0.1.6-beta

Reads introns from stdin (all_SRA_introns.tsv.gz), 
annotation files from command-line parameters and annotation from
GTF file(s) specified as argument(s) of --annotations; writes to stdout.
all_SRA_introns.tsv.gz should have AT LEAST the following tab-separated fields
on each line:
0. id line
1. chromosome
2. start position
3. end position
4. strand
5. 5' motif (left or donor)
6. 3' motif (right or acceptor)
(can include other fields after this, but are simply passed through
and appended to the end of the output line)

Tab-separated output written to stdout (unchanged unless noted):
0. id
1. chromosome
2. start position
3. end position
4. length of intron (new)
5. strand
6. 1 if junction is annotated else 0 (new)
7. left splice seq
8. right splice seq
9. 1 if left splice site is annotated else 0 (new)
10. 1 if right splice site is annotated else 0 (new)
everything else that was after the 3' motif column

stderr gets unannotated junctions; stdout gets annotated junctions

We executed:
gzip -cd all_SRA_introns.tsv.gz | pypy process_introns.py \
    --annotation [GTF files]
    >[output file]

We used the annotations (must be passed in this order):
gencode.v19.annotation.gtf.gz
    (from ftp://ftp.sanger.ac.uk/pub/gencode/Gencode_human/release_19/)
Homo_sapiens.GRCh37.75.gtf.gz
    (from ftp://ftp.ensembl.org/pub/release-75/gtf/homo_sapiens/)
refGene.gtf
    (downloaded according to instructions at 
     https://groups.google.com/a/soe.ucsc.edu/forum/#!msg/genome/
     bYEoa_hrSiI/cJ8WjnqXhlIJ ; uses command
     mysql --user=genome --host=genome-mysql.cse.ucsc.edu -A -N \ 
      -e "select * from refGene;" hg19 | cut -f2- | genePredToGtf
      file stdin refGene.gtf 

     see also: http://genomewiki.ucsc.edu/index.php/Genes_in_gtf_or_gff_format)
"""
import sys
import os
import subprocess
import struct
from operator import itemgetter
from bisect import bisect_right
from collections import defaultdict
import string


if __name__ == '__main__':
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('-t', '--annotated_type', type=int, required=False,
            default=2,
            help='print annotated (-t 0), unannotated (-t 1), '
                 'or both (-t 2) junctions'
        )
    parser.add_argument('--extract-splice-sites-path', type=str,
        default=os.path.join(os.path.dirname(__file__),
                                'extract_splice_sites.py'),
        help=('path to extract_splice_sites.py from HISAT v0.1.6-beta.'))
    parser.add_argument('--annotations', type=str, required=True, nargs='+',
            help='space-separated paths to GTF files encoding known junctions'
        )
    args = parser.parse_args()

    annotated_junctions = {}
    five_p = {}
    three_p = {}
    refs = ['chr' + str(i) for i in xrange(1, 23)] + ['chrM', 'chrX', 'chrY']
    types=['ES','UC','RG']
    for index,annotation in enumerate(args.annotations):
        extract_process = subprocess.Popen([sys.executable,
                                                args.extract_splice_sites_path,
                                                annotation],
                                                stdout=subprocess.PIPE)
        for line in extract_process.stdout:
            tokens = line.strip().split('\t')
            tokens[1] = str(int(tokens[1]) + 2)
            tokens[2] = str(int(tokens[2]))
            #sys.stderr.write("index %d line %s\n" % (index,line))
            tokens.append(types[index])
            if not tokens[0].startswith('chr'):
                tokens[0] = 'chr' + tokens[0]
            if tokens[0] in refs:
                hkey = tuple(tokens[:3])
                if hkey not in annotated_junctions:
                    annotated_junctions[hkey]=[]
                annotated_junctions[hkey].append(tokens[4])
                hkey = (tokens[0], tokens[1])
                if hkey not in five_p:
                    five_p[hkey]=[]
                five_p[hkey].append(tokens[4])
                #five_p.add((tokens[0], tokens[1]))
                hkey = (tokens[0], tokens[2])
                if hkey not in three_p:
                    three_p[hkey]=[]
                three_p[hkey].append(tokens[4])
                #three_p.add((tokens[0], tokens[2]))
        extract_process.stdout.close()
        exit_code = extract_process.wait()
        if exit_code != 0:
            raise RuntimeError(
                'extract_splice_sites.py had nonzero exit code {}.'.format(
                                                                    exit_code
                                                                )
            )
    #sys.stderr.write("Header:\n")
    sys.stderr.write('\t'.join(["gigatron_id","chromosome","start","end","length","strand","annotated?","left_motif","right_motif","left_annotated?","right_annotated?","samples","read_coverage_by_sample","samples_count","coverage_sum","coverage_avg","coverage_median","\n"]))
    for line in sys.stdin:
        tokens = line.strip().split('\t')
        if tokens[0] == 'gigatron_id_i':
		continue
        junction = tuple(tokens[1:4])
        #check to see if we want this junction
        annotated = junction in annotated_junctions
        annot_type = None
        if annotated:
            annot_type = annotated_junctions[junction]
        start = int(junction[1])
        length = int(junction[2]) + 1 - start
        strand = tokens[4]
	tokens_length = len(tokens)
        left_motif, right_motif = tokens[5], tokens[6]
	middle_stuff = tokens[7:]
        if (junction[0], junction[1]) in five_p:
            five_atype = five_p[(junction[0], junction[1])]
        if (junction[0], junction[2]) in three_p:
            three_atype = three_p[(junction[0], junction[2])]
        print '\t'.join([tokens[0], '\t'.join(junction), str(length), strand,
            '1' if annotated else '0', left_motif, right_motif,
            "%s:1" % (",".join(five_atype)) if (junction[0], junction[1]) in five_p else '0',
            "%s:1" % (",".join(three_atype)) if (junction[0], junction[2]) in three_p else '0',
	    '\t'.join(middle_stuff)])
