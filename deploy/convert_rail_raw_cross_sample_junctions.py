#!/usr/bin/env python2.7

import sys
import gzip
import argparse
import re

"""
Reformats raw cross sample Rail junctions
into Snaptron compatible format with
all samples collapsed into a comma-delimited
list of sample_id:coverage.
"""

# This code is taken from bowtie_index.py in Rail-RNA
import os
import struct
import mmap
from operator import itemgetter
from collections import defaultdict
from bisect import bisect_right
import csv

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
        self.rname_to_string = {}
        self.string_to_rname = {}
        for i, (rname, _) in enumerate(sorted_rnames):
            rname_string = ('%012d' % i)
            self.rname_to_string[rname] = rname_string
            self.string_to_rname[rname_string] = rname
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

def write_sample_ID_map(args, junction_line):
    fields = junction_line.rstrip().split("\t")
    samples = fields[1:]
    with open(args.input_file + ".samples2ids","w") as fout:
        fout.write("rail_id\tRun\n")
        for (idx,s) in enumerate(samples):
            subids = s.split("-")
            srr = s
            if len(subids) == 2 and subids[0][:3] == 'SRR':
                srr = subids[0]
            fout.write(str(idx)+"\t"+str(srr)+"\n")
    return samples


#need to support the format of both second and first pass junctions
junction_parser_map={True:re.compile(r'^(chr\d?[\dXYM]);([+-]);(\d+);(\d+)'), False: re.compile(r'^(chr\d?[\dXYM])([+-])\t(\d+)\t(\d+)\t([\d,]+)\t([\d,]+)$')}
def process_junction_fields(args, junction_line):
    fields = junction_line.rstrip().split("\t")
    junction_parser = junction_parser_map[args.second_pass]
    m = junction_parser.search(junction_line)
    (chrom,strand,start,end) = (m.group(1),m.group(2),m.group(3),m.group(4))
    sample_fields = []
    covs = []
    sum_ = 0
    covs_temp = []
    sids = []
    if args.second_pass:
        covs_temp = fields[1:]
        sids = xrange(0,len(covs_temp))
    else:
        sids = m.group(5).split(',')
        covs_temp = m.group(6).split(',')
    for (idx,cov) in enumerate(covs_temp):
        cov_ = int(cov)
        sid = str(sids[idx])
        if cov_ > 0:
            sample_fields.append(sid+":"+cov)
            covs.append(cov_)
            sum_ += cov_
    return (chrom,strand,start,end,sample_fields,sum_,covs)


def sample_summary_stats(sum_, covs):
    covs = sorted(covs)
    count = len(covs)
    median = int(count/2)
    if count % 2 == 0:
        median = round((covs[median-1] + covs[median])/2.0, 3)
    else:
        median = covs[median]
    avg = round(sum_/float(count), 3)
    return (count, avg, median)


def main():
    parser = argparse.ArgumentParser(description=__doc__, 
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--second-pass', action='store_const', const=True, default=False,
        help='if running on the second pass junctions produced by Rail')
    parser.add_argument('--input-file', type=str, required=True,
        help='path to Rail junctions file')
    parser.add_argument('--data-src', type=str, required=False, default="0", 
        help='integer ID identifying the compilation/source')
    parser.add_argument('--bowtie-idx', type=str, required=True,
        help='path to Bowtie index basename')
    args = parser.parse_args()
    
    #setup reference for motif scraping
    reference_index = BowtieIndexReference(args.bowtie_idx)
    reversed_complements = {
            ('CT', 'AC') : ('GT', 'AG'),
            ('CT', 'GC') : ('GC', 'AG'),
            ('GT', 'AT') : ('AT', 'AC')
        }

    samples=[]
    with gzip.open(args.input_file) as f:
        snaptron_id = 0
        for line in f:
            if args.second_pass and len(samples) == 0:
                samples = write_sample_ID_map(args, line)
                continue
            (chrom,strand,start,end,sample_fields,sum_,covs) = process_junction_fields(args, line)
            (count, avg, median) = sample_summary_stats(sum_, covs)
            jlength = (int(end) - int(start)) + 1
            sample_fields = ","+",".join(sample_fields)
            #will annotate in a later script
            annotated = 0
            annot_l = "0"
            annot_r = "0"
            motif_l = reference_index.get_stretch(chrom, int(start) - 1, 2)
            motif_r = reference_index.get_stretch(chrom, int(end) - 2, 2)
            if strand == '-':
                motif_l, motif_r = reversed_complements[(motif_l, motif_r)]
            sys.stdout.write("\t".join([str(x) for x in [snaptron_id,chrom,start,end,jlength,strand,annotated,motif_l,motif_r,annot_l,annot_r,sample_fields,count,sum_,"%.3f"%avg,"%.3f"%median,args.data_src]]) + "\n")
            snaptron_id += 1

        
if __name__ == '__main__':
    main()
    
