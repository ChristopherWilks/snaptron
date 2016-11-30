#!/usr/bin/env python

import subprocess
import tarfile
import tempfile
import atexit
import shutil
import glob
import os
import gzip
import sys

liftover_cmd='/data2/liftover/liftover'
liftover_chain='/data2/liftover/hg38ToHg19.over.chain'
unmapped_file='./couldnt_lift_over.tsv'
extract_destination='./'


refs = set(
            ['chr' + str(i) for i in xrange(1, 23)] + ['chrM', 'chrX', 'chrY']
        )

def liftover_junctions(inputf):
    annotated_junctions_hg19=[]
    temp_hg38 = os.path.join(extract_destination, 'hg38.bed')
    temp_hg19 = os.path.join(extract_destination, 'hg19.bed')
    annotated_junctions_hg38=gzip.open(inputf,"r")
    with open(temp_hg38, 'w') as hg38_stream:
        for i, junction in enumerate(annotated_junctions_hg38):
            junction = junction.rstrip().split('\t')
            print >>hg38_stream, '{}\t{}\t{}\tdummy_{}\t{}\t{}'.format(
                    junction[2], junction[3], junction[4], i, ";;".join([junction[1],junction[5],";;".join(junction[7:])]) , junction[6]
                )
    cmds = " ".join([
                                            liftover_cmd,
                                            temp_hg38,
                                            liftover_chain,
                                            temp_hg19,
                                            unmapped_file
                                        ])
    sys.stderr.write("cmd %s\n" % cmds)
    liftover_process = subprocess.call(' '.join([
                                            liftover_cmd,
                                            temp_hg38,
                                            liftover_chain,
                                            temp_hg19,
                                            unmapped_file
                                        ]),
                                        shell=True,
                                        executable='/bin/bash'
                                    )
    annotated_junctions_hg38.close()
    with open(temp_hg19) as hg19_stream:
        for line in hg19_stream:
            chrom, start, end, name, score, strand = line.strip().split('\t')[:6]
            #extract extra fields
            ef = score.split(';;')
            if chrom in refs:
                sys.stdout.write("%s\n" % "\t".join(["1",ef[0], chrom, start, end, ef[1], strand, "\t".join(ef[2:])]))
            else:
                print >>sys.stderr, '({}, {}, {}) not recorded.'.format(chrom, start, end)

if __name__ == '__main__':
    inputf = sys.argv[1]
    liftover_junctions(inputf) 
