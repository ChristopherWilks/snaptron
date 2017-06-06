#!/usr/bin/env python
"""
rip_annotated_junctions.py

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

http://hgdownload.cse.ucsc.edu/goldenPath/hg38/liftOver/
    hg38ToHg19.over.chain.gz

and liftOver executable available from
    https://genome-store.ucsc.edu/products/ .

Stats are written to stderr; we store them in
    annotated_junctions_stats.txt. We store hg38 regions that do not
    map to hg19 in unmapped_hg38.bed .

From the runs/sra/v2 directory, we ran

pypy rip_annotated_junctions.py
    --hisat2-dir /path/to/hisat2-2.0.1-beta
    --annotations path/to/jan_24_2016_annotations.tar.gz
    --chain /path/to/hg19ToHg38.over.chain
    --liftover /path/to/liftOver
    --unmapped unmapped_hg19.bed 2>annotated_junctions_stats.txt
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

file2source = {"hg19/gencode.v19.annotation.gtf.gz":"gC19","hg19/refGene.txt.gz":"rG19","hg19/acembly.txt.gz":"aC19","hg19/ccdsGene.txt.gz":"cG19","hg19/vegaGene.txt.gz":"vG19","hg19/knownGene.txt.gz":"kG19","hg19/mgcGenes.txt.gz":"mG19","hg19/lincRNAsTranscripts.txt.gz":"lR19","hg19/sibGene.txt.gz":"sG19","hg38/refGene.txt.gz":"rG38","hg38/ccdsGene.txt.gz":"cG38","hg38/gencode.v24.annotation.gtf.gz":"gC38","hg38/knownGene.txt.gz":"kG38","hg38/mgcGenes.txt.gz":"mG38","hg38/lincRNAsTranscripts.txt.gz":"lR38","hg38/sibGene.txt.gz":"sG38"}

if __name__ == '__main__':
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('--hisat2-dir', type=str, required=True,
            help=('path to directory containing contents of HISAT2; we '
                  'unpacked ftp://ftp.ccb.jhu.edu/pub/infphilo/hisat2/'
                  'downloads/hisat2-2.0.0-beta-Linux_x86_64.zip to get this')
        )
    parser.add_argument('--annotations', type=str, required=True,
            help=('annotations archive; this should be '
                  'jan_24_2016_annotations.tar.gz')
        )
    parser.add_argument('--liftover', type=str, required=True,
            help=('path to liftOver executable available from '
                  'https://genome-store.ucsc.edu/products/')
        )
    parser.add_argument('--chain', type=str, required=True,
            help=('path to unzipped liftover chain; this should be '
                  'hg38ToHg19.over.chain')
        )
    parser.add_argument('--unmapped', type=str, required=True,
            help='BED in which unmapped junctions should be stored'
        )
    args = parser.parse_args()
    extract_destination = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, extract_destination)
    with tarfile.open(args.annotations, 'r:gz') as tar:
        tar.extractall(path=extract_destination)
    extract_splice_sites_path = os.path.join(args.hisat2_dir,
                                                'extract_splice_sites.py')
    containing_dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(containing_dir, 'hg38.sizes')) as hg38_stream:
        refs = set(
                [tokens.strip().split('\t')[0] for tokens in hg38_stream]
            )
    annotated_junctions_hg19 = set()
    annotated_junctions_hg38 = set()
    for junction_file in glob.glob(
                os.path.join(extract_destination, 'anno', 'hg*', '*')
            ):
        label = (('hg19/' if 'hg19' in junction_file else 'hg38/')
                        + os.path.basename(junction_file))
        datasource_code = file2source[label]
        unique_junctions = set()
        if 'hg38' in junction_file:
            annotated_junctions = annotated_junctions_hg38
        else:
            annotated_junctions = annotated_junctions_hg19
        if 'gencode' in junction_file:
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
                annotated_junctions.add(junction_to_add)
                unique_junctions.add(junction_to_add)
            extract_process.stdout.close()
            exit_code = extract_process.wait()
            if exit_code != 0:
                raise RuntimeError(
                    'extract_splice_sites.py had nonzero exit code {}.'.format(
                                                                    exit_code
                                                                )
                )
        else:
            if 'knownGene' in junction_file:
                offset = 0
            else:
                offset = 1
            for line in gzip.open(junction_file):
                tokens = line.strip().split('\t')
                exons = [(int(start), int(end)) for start, end in
                                zip(tokens[8+offset].split(','),
                                    tokens[9+offset].split(','))[:-1]]
                junctions_to_add = [
                        (tokens[1+offset], exons[i-1][1] + 1, exons[i][0],
                            tokens[2+offset], datasource_code)
                        for i in xrange(1, len(exons))
                    ]
                final_junctions_to_add = []
                for junction in junctions_to_add:
                    if junction[2] < junction[1]:
                        print >>sys.stderr, (
                                'Invalid junction ({}, {}, {}) from file {}. '
                                'Skipping.'
                            ).format(
                                    junction[0], junction[1], junction[2],
                                    junction_file
                                )
                        continue
                    final_junctions_to_add.append(junction)
                annotated_junctions.update(final_junctions_to_add)
                unique_junctions.update(final_junctions_to_add)
        print >>sys.stderr, 'Junctions in {}: {}'.format(
                label,
                len(unique_junctions)
            )

    # Convert from hg19 to hg38
    temp_hg19 = os.path.join(extract_destination, 'hg19.bed')
    temp_hg38 = os.path.join(extract_destination, 'hg38.bed')
    with open(temp_hg19, 'w') as hg19_stream:
        for i, junction in enumerate(annotated_junctions_hg19):
            # Handle incorrect junctions
            #print >>hg19_stream, '{}\t{}\t{}\tdummy_{}\t1\t{}'.format(
            print >>hg19_stream, '{}\t{}\t{}\t{}\t1\t{}'.format(
                    junction[0], junction[1], junction[2], junction[4], junction[3]
                )
    liftover_process = subprocess.check_call(' '.join([
                                            args.liftover,
                                            temp_hg19,
                                            args.chain,
                                            temp_hg38,
                                            args.unmapped
                                        ]),
                                        shell=True,
                                        executable='/bin/bash'
                                    )
    # Add all new junctions to hg38 set
    before_liftover = len([junction for junction
                            in annotated_junctions_hg38
                            if junction[0] in refs])
    print >>sys.stderr, ('Below, if an RNAME is not in the chromosomal '
                         'assembly, it\'s ignored.')
    with open(temp_hg38) as hg38_stream:
        for line in hg38_stream:
            chrom, start, end, name, score, strand = line.strip().split(
                                                                    '\t'
                                                                )[:6]
            if chrom in refs:
                annotated_junctions_hg38.add(
                    (chrom, int(start), int(end), strand, name)
                )
            else:
                print >>sys.stderr, '({}, {}, {}, {}) not recorded.'.format(
                                            chrom, start, end, name
                                        )
    after_liftover = len([junction for junction
                            in annotated_junctions_hg38
                            if junction[0] in refs])
    print >>sys.stderr, ('hg38 annotations contributed {} junctions, and '
                         'liftover of hg19 annotations contributed an '
                         'additional {} junctions.').format(
                                before_liftover,
                                after_liftover - before_liftover
                            )
    junc2datasource = {}
    for junction in annotated_junctions_hg38:
        if junction[0] in refs:
            if junction[:4] not in junc2datasource:
                junc2datasource[junction[:4]]=set()
            junc2datasource[junction[:4]].add(junction[4])
    seen = set()
    for junction in annotated_junctions_hg38:
        if junction[0] in refs and junction[:4] not in seen:
            sources = ",".join(sorted(junc2datasource[junction[:4]]))
            print "%s\t%s" % ('\t'.join(map(str, junction[:4])),sources)
            seen.add(junction[:4])
