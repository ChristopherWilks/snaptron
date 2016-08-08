#!/usr/bin/env python2.7
import sys
import re
from collections import namedtuple
import gzip
import snapconf
import snannotation

BREAKPOINT_COLUMN = 11
breakpoint_pattern = re.compile(r'^([^{]+){([^}]+)}:r.([^{]+){([^}]+)}:r\.(.+)$')
BreakPoint = namedtuple('BreakPoint','gname1 gid1 g1start g1end intron_coord1 exon_offset1 genomic_range1 antisense1 gname2 gid2 g2start g2end intron_coord2 exon_offset2 genomic_range2 antisense2')

#normal exon2exon fusion
#CCDC6{ENST00000263102}:r.1_535_RET{ENST00000355710}:r.2369_5659
#unknown breakpoint fusion
#PAX8{NM_003    466.2}:r.?_PPARG{NM_015869.2}:r.?
#TMPRSS2 from exon 1 (UTR) to ERG exon 2 (inclusive).
#TMPRSS2{NM_005656.2}:r.1_71_ERG{NM_004449.3}:r.38_3097
#TRMPSS2 from intron after exon 5 to intron before ERG exon 3, intronic breakpoints NOT known (but remarked on in the paper).
#TMPRSS2{NM_005656.2}:r.1_71+?_ERG{NM_004449.3}:r.38-?_3097
#TMPRSS2 from intron after exon 1 to intron before exon 2, intronic breakpoints known (374bp downstream of TMPRSS2 exon 1 and 54bp upstream of ERG exon 2).
#TMPRSS2{NM_005656.2}:r.1_71+374_ERG{NM_004449.3}:r.38-54_3097
#TMPRSS2 present in sense orientation, ERG in the antisense., same for when in intron ("o" signifies antisense orientation)
#TMPRSS2{NM_005656.2}:r.1_71_oERG{NM_004449.3}:r.38_3097

def decode_cosmic_mrna_coord_format(mrna_coord_str, first_gene=True):
    fields = mrna_coord_str.split('_')
    gname2 = None
    if first_gene:
        gname2 = fields.pop(-1)
    gend = fields.pop(-1)
    if gend == '?':
        raise RuntimeError("no coordinate available in breakpoint string %s from COSMIC" % (mrna_coord_str))
    gstart = fields[-1]
    fields = []
    fields = gstart.split('-')
    if first_gene:
        fields = gend.split('+')
    #check if breakpoint in intron for current gene
    intron_coord = -1
    if len(fields) > 1 and fields[1] != '?':
        intron_coord = fields[1]
    if first_gene:
        gend = fields[0]
    else:
        gstart = fields[0]
    return (gname2, int(gstart), int(gend), int(intron_coord))

def is_gene_breakpoint_antisense(gname):
    if gname[0] == 'o':
        return (gname[1:],True)
    return (gname,False)


def decode_cosmic_fusion_breakpoint_format(breakpoint_str, transcript_map):
    #TODO: support 3 or more region breakpoints
    m = breakpoint_pattern.search(breakpoint_str) 
    if m is not None:
        gname1 = m.group(1)
        gid1 = m.group(2)
        mcoords1_gname2 = m.group(3)
        gid2 = m.group(4)
        mcoords2 = m.group(5)
       
        #now decode the first gene's mrna coords + the second gene's name mixture
        (gname2, g1start, g1end, intron_coord1) = decode_cosmic_mrna_coord_format(mcoords1_gname2)
        (_, g2start, g2end, intron_coord2) = decode_cosmic_mrna_coord_format(mcoords2, first_gene=False)
        (gname1, antisense1) = is_gene_breakpoint_antisense(gname1)
        (gname2, antisense2) = is_gene_breakpoint_antisense(gname2)
       
        #now we need the genomic range for the exon sub-span of the transcript (inclusive) which are either in or outside of the fusion gene
        brk_group = []
        norm_group = []

        (exon_offset1, brk_range1, norm_range1) = map_mrna2genomic_coord(gid1, g1end, transcript_map, first_gene=True)
        brk_group.append(brk_range1)
        norm_group.append(norm_range1)

        (exon_offset2, brk_range2, norm_range2) = map_mrna2genomic_coord(gid2, g2start, transcript_map, first_gene=False)
        brk_group.append(brk_range2)
        norm_group.append(norm_range2)
         
        return (brk_group, norm_group, BreakPoint(gname1, gid1, g1start, g1end, intron_coord1, exon_offset1, brk_group[0], antisense1, gname2, gid2, g2start, g2end, intron_coord2, exon_offset2, brk_group[1], antisense2))


def prepare_final_range(chrom,strand, e1start, e1end, e2start, e2end):
    #default start/end
    start = e1start
    end = e2end
    #swap so we always have start <= end
    if strand == '-':
        start = e2start
        end = e1end
    return "%s:%d-%d" % (chrom, int(start), int(end))

def determine_genomic_range_for_outside_breakpoint(chrom, strand, transcript_coords, last_exon, first_gene=True):
    (e1start,e1end) = transcript_coords[last_exon]
    (e2start,e2end) = transcript_coords[-1]
    #breakpoint exon end+1 thru end of transcript
    if first_gene:
        e1start_old = e1start
        e1start = int(e1end) + 1
        e1end = int(e1start_old) - 1 #only for reverse
    #transcript start thru breakpoint exon start-1
    else:
        e2start = int(e1end) + 1 #only for reverse
        e2end = int(e1start) - 1 
        (e1start,e1end) = transcript_coords[0]
    return prepare_final_range(chrom, strand, e1start, e1end, e2start, e2end)

def determine_genomic_range_for_breakpoint(chrom, strand, transcript_coords, last_exon, first_gene=True):
    #transcript start thru breakpoint exon end
    (e1start,e1end) = transcript_coords[0]
    (e2start,e2end) = transcript_coords[last_exon]
    #breakpoint exon start thru end of transcript
    if not first_gene:
        (e1start,e1end) = (e2start,e2end)
        (e2start,e2end) = transcript_coords[-1]
    return prepare_final_range(chrom, strand, e1start, e1end, e2start, e2end)

def map_mrna2genomic_coord(gid, mrna_coord, transcript_map, first_gene=True):
    if gid not in transcript_map:
        return (None, None)
    (chrom, strand, transcript_coords) = transcript_map[gid]
    toffset = 0
    last_exon = 0
    eidx = 0
    #assume transcript coords are sorted in correct order based on strand
    #TODO: could speed this up using a binary search, not necessary at this time
    for (s1,e1) in transcript_coords:
        poffset = toffset+1
        #calculate offset for the span of this current exon
        #assume 1-based
        toffset += (int(e1) - int(s1)) + 1
        if mrna_coord >= poffset:
            last_exon = eidx
        if mrna_coord <= toffset:
            break
        eidx += 1 
    #now determine the full exon coordinate range from the original transcript for
    #this gene's part of the fusion
    brange = determine_genomic_range_for_breakpoint(chrom, strand, transcript_coords, last_exon, first_gene)
    nrange = determine_genomic_range_for_outside_breakpoint(chrom, strand, transcript_coords, last_exon, first_gene)
    return (last_exon, brange, nrange)

class CosmicFusions(object):

    def __init__(self, cosmic_fp):
        self.name2id = {}
        self.id2fusion = {}
        with gzip.open(cosmic_fp) as fin:
            for line in fin:
                line = line.rstrip()
                fields = line.split('\t')
                #only load the fusions with breakpoint info
                if len(fields[BREAKPOINT_COLUMN]) < 1:
                    continue
                self.id2fusion[fields[BREAKPOINT_COLUMN-1]] = fields
                m = breakpoint_pattern.search(fields[BREAKPOINT_COLUMN])
                if m is not None:
                    gname1 = m.group(1)
                    gid1 = m.group(2)
                    mcoords1_gname2 = m.group(3)
                    gid2 = m.group(4)
                    gname2 = mcoords1_gname2.split('_')[-1]
                    fusion_name = "%s-%s" % (gname1.upper(),gname2.upper())
                    if fusion_name not in self.name2id:
                        self.name2id[fusion_name] = set()
                    self.name2id[fusion_name].add(fields[BREAKPOINT_COLUMN-1])



def process_params(input_, cosmic_db):
    cosmic_fusion_id = None
    fields = input_.split('&')
    header = True
    cosmic_fusion_id = -1
    fusion = ""
    for field in fields:
        (fname,input_) = field.split('=')
        if fname == 'header':
            header = bool(int(input_))
            continue
        input_ = re.sub(r'^COSF(\d+)',r'\1',input_)
        try:
            cosmic_fusion_id = str(int(input_))
        except ValueError, ve:
            fusion_name = input_.upper()
            cosmic_fusion_ids = cosmic_db.name2id[fusion_name]
            if len(cosmic_fusion_ids) > 1:
                raise RuntimeError("more than one fusion ID for the name %s" % fusion_name)
        fusion = cosmic_db.id2fusion[cosmic_fusion_id]
    return (cosmic_fusion_id, fusion, header)


def main():
    input_ = sys.argv[1]
    try:
        cosmic_db = CosmicFusions(snapconf.COSMIC_FUSION_FILE)
        (cosmic_fusion_id, fusion_info, header) = process_params(input_, cosmic_db)
        breakpoint = fusion_info[BREAKPOINT_COLUMN]
        gc = snannotation.GeneCoords(load_refseq=False, load_canonical=False, load_transcript=True)
        (brks, norms, decoded_bp) = decode_cosmic_fusion_breakpoint_format(breakpoint, gc.transcript_map)
        if header:
            sys.stdout.write("region\tcontains\tgroup\n")
        for (i,norm) in enumerate(norms):
            sys.stdout.write("%s\t1\tAnormal_%d\n" % (norm,i+1))
        for (i,bp) in enumerate(brks):
            sys.stdout.write("%s\t1\tBbreakpoint_%d\n" % (bp,i+1))
    except KeyError, ke:
        sys.stderr.write("bad cosmic fusion id or name\n")
        sys.exit(-1)
    #want to avoid the full stacktrace for downstream users
    except RuntimeError, e:
        sys.stderr.write("%s\n" % str(e))
        sys.exit(-1)


if __name__ == '__main__':
    main()
