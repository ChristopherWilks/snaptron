#!/usr/bin/env python
"""
rip_annotated_junctions.py

Non-reference/species verson of this script, no lift-over

Rips junctions from annotation files contained in
jan_24_2016_annotations.tar.gz, as described in annotation_definition.md.
Junctions are dumped to stdout, which we record as annotated_junctions.tsv.gz
in runs/sra (same directory as this file). annotated_junctions.tsv.gz is
required by tables.py. The format of annotated_junctions.tsv.gz is

(tab-separated fields), one per junction
1. Chromosome
2. Start position (1-based, inclusive)
3. End position (1-based, inclusive)
4. Strand (+ or -)
5. anno source (abbreviation)

Must have

Stats are written to stderr

From the runs/sra/v2 directory, we ran

pypy rip_annotated_junctions.py
    --hisat2-dir /path/to/hisat2-2.0.1-beta
    --annotations path/to/jan_24_2016_annotations.tar.gz
    | sort -k1,1 -k2,2n -k3,3n | gzip >annotated_junctions.tsv.gz
"""

import subprocess
import tarfile
import argparse
import tempfile
import atexit
import shutil
import glob
import os
import gzip
import sys

#file2source = {"hg19/gencode.v19.annotation.gtf.gz":"gC19","hg19/refGene.txt.gz":"rG19","hg19/acembly.txt.gz":"aC19","hg19/ccdsGene.txt.gz":"cG19","hg19/vegaGene.txt.gz":"vG19","hg19/knownGene.txt.gz":"kG19","hg19/mgcGenes.txt.gz":"mG19","hg19/lincRNAsTranscripts.txt.gz":"lR19","hg19/sibGene.txt.gz":"sG19","hg38/refGene.txt.gz":"rG38","hg38/ccdsGene.txt.gz":"cG38","hg38/gencode.v24.annotation.gtf.gz":"gC38","hg38/knownGene.txt.gz":"kG38","hg38/mgcGenes.txt.gz":"mG38","hg38/lincRNAsTranscripts.txt.gz":"lR38","hg38/sibGene.txt.gz":"sG38"}

#file2source = {"mm10/mouse10_ucsc_genes.gtf.gz":"kG10","mm10/mouse10_gencodevm11_comp.gtf.gz":"gC11","mm10/mouse10_gencodevm09_comp.gtf.gz":"gC09","mm10/mouse10_refseq_refgene.gtf.gz":"rG10"}
file2source = {"mouse10_ucsc_genes.gtf.gz":"kG10","mouse10_gencodevm11_comp.gtf.gz":"gC11","mouse10_gencodevm09_comp.gtf.gz":"gC09","mouse10_refseq_refgene.gtf.gz":"rG10"}

if __name__ == '__main__':
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('--extract-script-dir', type=str, required=True,
            help=('path to directory containing extract_splice_sites.py script (from HISAT2)')
        )
    parser.add_argument('--annotations', type=str, required=True,
            help=('full path to directory that has the annotation GTF(s) in gzipped format')
        )
    args = parser.parse_args()
    extract_destination = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, extract_destination)
    #with tarfile.open(args.annotations, 'r:gz') as tar:
    #    tar.extractall(path=extract_destination)
    extract_splice_sites_path = os.path.join(args.extract_script_dir,
                                                'extract_splice_sites.py')
    containing_dir = os.path.dirname(os.path.realpath(__file__))
    annotated_junctions_ = set()
    for junction_file in glob.glob(
                os.path.join(args.annotations, '*')
            ):
        label = os.path.basename(junction_file)
        datasource_code = file2source[label]
        unique_junctions = set()
        #extract_splice_sites_path prints 0-based, exon coords around junctions
        #hence the +2 for the start here
        extract_process = subprocess.Popen(' '.join([
                                        sys.executable,
                                        extract_splice_sites_path,
                                        '<(gzip -cd %s)'
                                           % junction_file
                                    ]),
                                    shell=True,
                                    executable='/bin/bash',
                                    stdout=subprocess.PIPE
                                )
        for line in extract_process.stdout:
            tokens = line.strip().split('\t')
            tokens[1] = int(tokens[1]) + 2
            tokens[2] = int(tokens[2])
            if tokens[2] < tokens[1]:
                print >>sys.stderr, (
                        'Invalid junction ({}, {}, {}) from file {}. '
                        'Skipping.'
                    ).format(
                            tokens[0], tokens[1], tokens[2], junction_file
                        )
                continue
            tokens.append(datasource_code)
            junction_to_add = tuple(tokens)
            annotated_junctions_.add(junction_to_add)
            unique_junctions.add(junction_to_add)
        extract_process.stdout.close()
        exit_code = extract_process.wait()
        if exit_code != 0:
            raise RuntimeError(
                'extract_splice_sites.py had nonzero exit code {}.'.format(
                                                                exit_code
                                                            )
            )
        print >>sys.stderr, 'Junctions in {}: {}'.format(
                label,
                len(unique_junctions)
            )

    junc2datasource = {}
    for junction in annotated_junctions_:
        if junction[:4] not in junc2datasource:
            junc2datasource[junction[:4]]=set()
        junc2datasource[junction[:4]].add(junction[4])
    seen = set()
    for junction in annotated_junctions_:
        if junction[:4] not in seen:
            sources = ",".join(sorted(junc2datasource[junction[:4]]))
            print "%s\t%s" % ('\t'.join(map(str, junction[:4])),sources)
            seen.add(junction[:4])
