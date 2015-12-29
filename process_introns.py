#!/usr/bin/env python
"""
process_introns.py
Abhi Nellore
10/2/2015

Grabs intronic sequence for input introns and says whether they're in
annotation. Requires extract_splice_sites.py from HISAT v0.1.6-beta and
Bowtie 1 index for hg19.

Reads introns from stdin (all_SRA_introns.tsv.gz), 
annotation files from command-line parameters and annotation from
GTF file(s) specified as argument(s) of --annotations; writes to stdout.
all_SRA_introns.tsv.gz should have AT LEAST the following tab-separated fields
on each line:
1. chromosome
2. start position
3. end position
4. strand
5. 5' motif
6. 3' motif
...
next-to-last field: comma-separated list of sample indexes
last field: comma-separated list of read coverages corresponding to sample
    indexes

Tab-separated output written to stdout:
1. chromosome
2. start position
3. end position
4. strand
5. intronic sequence (from 5' end - left_pad to 3' end + right_pad)
6. 1 if junction is annotated else 0
7. intron type (GTAG, GCAG, ATAC)
8. 1 if 5' splice site is annotated else 0
9. 1 if 3' splice site is annotated else 0

stderr gets unannotated junctions; stdout gets annotated junctions

We executed:
gzip -cd all_SRA_introns.tsv.gz | pypy process_introns.py \
    --annotation [GTF files] --bowtie-idx [hg19 Bowtie 1 index basename]
    >[output file]

We used the annotations:
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
import random
#random.seed(1688)
import subprocess
import struct
import mmap
from operator import itemgetter
from bisect import bisect_right
from collections import defaultdict
import string
import cPickle

class BowtieIndexReference(object):
    """
    Given prefix of a Bowtie index, parses the reference names, parses the
    extents of the unambiguous stretches, and memory-maps the file containing
    the unambiguous-stretch sequences.  get_stretch member function can
    retrieve stretches of characters from the reference, even if the stretch
    contains ambiguous characters.
    """

    def __init__(self, idx_prefix):

        # Open file handles
        if os.path.exists(idx_prefix + '.3.ebwt'):
            # Small index (32-bit offsets)
            fh1 = open(idx_prefix + '.1.ebwt', 'rb')  # for ref names
            fh3 = open(idx_prefix + '.3.ebwt', 'rb')  # for stretch extents
            fh4 = open(idx_prefix + '.4.ebwt', 'rb')  # for unambiguous sequence
            sz, struct_unsigned = 4, struct.Struct('I')
        else:
            raise RuntimeError('No Bowtie index files with prefix "%s"' % idx_prefix)

        #
        # Parse .1.bt2 file
        #
        one = struct.unpack('<i', fh1.read(4))[0]
        assert one == 1

        ln = struct_unsigned.unpack(fh1.read(sz))[0]
        line_rate = struct.unpack('<i', fh1.read(4))[0]
        lines_per_side = struct.unpack('<i', fh1.read(4))[0]
        _ = struct.unpack('<i', fh1.read(4))[0]
        ftab_chars = struct.unpack('<i', fh1.read(4))[0]
        _ = struct.unpack('<i', fh1.read(4))[0]

        nref = struct_unsigned.unpack(fh1.read(sz))[0]
        # get ref lengths
        reference_length_list = []
        for i in xrange(nref):
            reference_length_list.append(struct.unpack('<i', fh1.read(sz))[0])

        nfrag = struct_unsigned.unpack(fh1.read(sz))[0]
        # skip rstarts
        fh1.seek(nfrag * sz * 3, 1)

        # skip ebwt
        bwt_sz = ln // 4 + 1
        line_sz = 1 << line_rate
        side_sz = line_sz * lines_per_side
        side_bwt_sz = side_sz - 8
        num_side_pairs = (bwt_sz + (2*side_bwt_sz) - 1) // (2*side_bwt_sz)
        ebwt_tot_len = num_side_pairs * 2 * side_sz
        fh1.seek(ebwt_tot_len, 1)

        # skip zOff
        fh1.seek(sz, 1)

        # skip fchr
        fh1.seek(5 * sz, 1)

        # skip ftab
        ftab_len = (1 << (ftab_chars * 2)) + 1
        fh1.seek(ftab_len * sz, 1)

        # skip eftab
        eftab_len = ftab_chars * 2
        fh1.seek(eftab_len * sz, 1)

        refnames = []
        while True:
            refname = fh1.readline()
            if len(refname) == 0 or ord(refname[0]) == 0:
                break
            refnames.append(refname.split()[0])
        assert len(refnames) == nref

        #
        # Parse .3.bt2 file
        #
        one = struct.unpack('<i', fh3.read(4))[0]
        assert one == 1

        nrecs = struct_unsigned.unpack(fh3.read(sz))[0]

        running_unambig, running_length = 0, 0
        self.recs = defaultdict(list)
        self.offset_in_ref = defaultdict(list)
        self.unambig_preceding = defaultdict(list)
        length = {}

        ref_id, ref_namenrecs_added = 0, None
        for i in xrange(nrecs):
            off = struct_unsigned.unpack(fh3.read(sz))[0]
            ln = struct_unsigned.unpack(fh3.read(sz))[0]
            first_of_chromosome = ord(fh3.read(1)) != 0
            if first_of_chromosome:
                if i > 0:
                    length[ref_name] = running_length
                ref_name = refnames[ref_id]
                ref_id += 1
                running_length = 0
            assert ref_name is not None
            self.recs[ref_name].append((off, ln, first_of_chromosome))
            self.offset_in_ref[ref_name].append(running_length)
            self.unambig_preceding[ref_name].append(running_unambig)
            running_length += (off + ln)
            running_unambig += ln

        length[ref_name] = running_length
        assert nrecs == sum(map(len, self.recs.itervalues()))

        #
        # Memory-map the .4.bt2 file
        #
        ln_bytes = (running_unambig + 3) // 4
        self.fh4mm = mmap.mmap(fh4.fileno(), ln_bytes, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ)

        # These are per-reference
        self.length = length
        self.refnames = refnames

        # To facilitate sorting reference names in order of descending length
        sorted_rnames = sorted(self.length.items(),
                               key=lambda x: itemgetter(1)(x), reverse=True)
        '''A case-sensitive sort is also necessary here because new versions of
        bedGraphToBigWig complain on encountering a nonlexicographic sort
        order.'''
        lexicographically_sorted_rnames = sorted(self.length.items(),
                                                    key=lambda x:
                                                    itemgetter(0)(x))
        self.rname_to_string, self.l_rname_to_string = {}, {}
        self.string_to_rname, self.l_string_to_rname = {}, {}
        for i, (rname, _) in enumerate(sorted_rnames):
            rname_string = ('%012d' % i)
            self.rname_to_string[rname] = rname_string
            self.string_to_rname[rname_string] = rname
        for i, (rname, _) in enumerate(lexicographically_sorted_rnames):
            rname_string = ('%012d' % i)
            self.l_rname_to_string[rname] = rname_string
            self.l_string_to_rname[rname_string] = rname
        # Handle unmapped reads
        unmapped_string = ('%012d' % len(sorted_rnames))
        self.rname_to_string['*'] = unmapped_string
        self.string_to_rname[unmapped_string] = '*'

        # For compatibility
        self.rname_lengths = self.length

    def get_stretch(self, ref_id, ref_off, count):
        """
        Return a stretch of characters from the reference, retrieved
        from the Bowtie index.

        @param ref_id: name of ref seq, up to & excluding whitespace
        @param ref_off: offset into reference, 0-based
        @param count: # of characters
        @return: string extracted from reference
        """
        assert ref_id in self.recs
        # Account for negative reference offsets by padding with Ns
        N_count = min(abs(min(ref_off, 0)), count)
        stretch = ['N'] * N_count
        count -= N_count
        if not count: return ''.join(stretch)
        ref_off = max(ref_off, 0)
        starting_rec = bisect_right(self.offset_in_ref[ref_id], ref_off) - 1
        assert starting_rec >= 0
        off = self.offset_in_ref[ref_id][starting_rec]
        buf_off = self.unambig_preceding[ref_id][starting_rec]
        # Naive to scan these records linearly; obvious speedup is binary search
        for rec in self.recs[ref_id][starting_rec:]:
            off += rec[0]
            while ref_off < off and count > 0:
                stretch.append('N')
                count -= 1
                ref_off += 1
            if count == 0:
                break
            if ref_off < off + rec[1]:
                # stretch extends through part of the unambiguous stretch
                buf_off += (ref_off - off)
            else:
                buf_off += rec[1]
            off += rec[1]
            while ref_off < off and count > 0:
                buf_elt = buf_off >> 2
                shift_amt = (buf_off & 3) << 1
                stretch.append(
                    'ACGT'[(ord(self.fh4mm[buf_elt]) >> shift_amt) & 3]
                )
                buf_off += 1
                count -= 1
                ref_off += 1
            if count == 0:
                break
        # If the requested stretch went past the last unambiguous
        # character in the chromosome, pad with Ns
        while count > 0:
            count -= 1
            stretch.append('N')
        return ''.join(stretch)

if __name__ == '__main__':
    import argparse
    # Print file's docstring if -h is invoked
    parser = argparse.ArgumentParser(description=__doc__, 
                formatter_class=argparse.RawDescriptionHelpFormatter)
    # Add command-line arguments
    parser.add_argument('-x', '--bowtie-idx', type=str, required=True,
            help='Bowtie 1 index basename'
        )
    parser.add_argument('-f', '--filter', type=int, required=False,
            default=5,
            help='minimum number of reads in which a junction must appear '
                 'across samples for it to be written to an output stream'
        )
    parser.add_argument('-t', '--annotated_type', type=int, required=False,
            default=2,
            help='print annotated (-t 0), unannotated (-t 1), '
                 'or both (-t 2) junctions'
        )
    parser.add_argument('-l', '--left-pad', type=int, required=False,
            default=50,
            help='number of bases by which to pad intronic sequence on 5\' '
                 'end'
        )
    parser.add_argument('-r', '--right-pad', type=int, required=False,
            default=50,
            help='number of bases by which to pad intronic sequence on 3\' '
                 'end'
        )
    parser.add_argument('--extract-splice-sites-path', type=str,
        default=os.path.join(os.path.dirname(__file__),
                                'extract_splice_sites.py'),
        help=('path to extract_splice_sites.py from HISAT v0.1.6-beta.'))
    parser.add_argument('--annotations', type=str, required=True, nargs='+',
            help='space-separated paths to GTF files encoding known junctions'
        )
    args = parser.parse_args()

    annotated_junctions = set()
    five_p = set()
    three_p = set()
    refs = ['chr' + str(i) for i in xrange(1, 23)] + ['chrM', 'chrX', 'chrY']
    for annotation in args.annotations:
        extract_process = subprocess.Popen([sys.executable,
                                                args.extract_splice_sites_path,
                                                annotation],
                                                stdout=subprocess.PIPE)
        for line in extract_process.stdout:
            tokens = line.strip().split('\t')
            tokens[1] = str(int(tokens[1]) + 2)
            tokens[2] = str(int(tokens[2]))
            if not tokens[0].startswith('chr'):
                tokens[0] = 'chr' + tokens[0]
            if tokens[0] in refs:
                annotated_junctions.add(tuple(tokens[:-1]))
                five_p.add((tokens[0], tokens[1]))
                three_p.add((tokens[0], tokens[2]))
        extract_process.stdout.close()
        exit_code = extract_process.wait()
        if exit_code != 0:
            raise RuntimeError(
                'extract_splice_sites.py had nonzero exit code {}.'.format(
                                                                    exit_code
                                                                )
            )

    reference_index = BowtieIndexReference(args.bowtie_idx)
    reversed_complement_translation_table = string.maketrans('ACGT', 'TGCA')
    for line in sys.stdin:
        tokens = line.strip().split('\t')
        junction = tuple(tokens[:3])
        #check to see if we want this junction
        annotated = junction in annotated_junctions
        #annotated = random.randint(0,1)
        if int(annotated) == args.annotated_type:
            continue
        start = int(junction[1])
        length = int(junction[2]) + 1 - start
        strand = tokens[3]
        left_motif, right_motif = tokens[4], tokens[5]
        #read_count = sum([int(token) for token in tokens[-1].split(',')])
        read_count = len(tokens[-1].split(','))
        if read_count < args.filter:
            continue
        intronic_sequence = reference_index.get_stretch(
                    junction[0], -args.left_pad + start - 1,
                    length + args.right_pad + args.left_pad
                )
        if strand == '-':
            intronic_sequence = intronic_sequence[::-1].translate(
                    reversed_complement_translation_table
                )
        else:
            assert strand == '+'
        #print '\t'.join(junction + (strand, intronic_sequence,
        print '\t'.join(junction + (strand,
            '1' if annotated else '0', left_motif + right_motif,
            #str(annotated), left_motif + right_motif,
            '1' if (junction[0], junction[1]) in five_p else '0',
            '1' if (junction[0], junction[2]) in three_p else '0'))
