#!/usr/bin/env python2.7
import sys
import re
from collections import namedtuple

BreakPoint = namedtuple('BreakPoint','gname1 gid1 g1start g1end intron_coord1 exon_offset1 genomic_coord1 antisense1 gname2 gid2 g2start g2end intron_coord2 exon_offset2 genomic_coord2 antisense2')

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
    gstart = fields[-1]
    fields = []
    fields = gstart.split('-')
    if first_gene:
        fields = gend.split('+')
    #check if breakpoint in intron for current gene
    intron_coord = -1
    if len(fields) > 1:
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

breakpoint_pattern = re.compile(r'^([^{]+){([^}]+)}:r.([^{]+){([^}]+)}:r\.(.+)$')
def decode_cosmic_fusion_breakpoint_format(breakpoint_str, transcript_map):
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
        
        (exon_offset1, exon_gcoords) = map_mrna2genomic_coord(gid1, g1end, transcript_map)
        genomic_coord1 = int(exon_gcoords[1])
        (exon_offset2, exon_gcoords) = map_mrna2genomic_coord(gid2, g2start, transcript_map)
        genomic_coord2 = int(exon_gcoords[0])
         
        return BreakPoint(gname1, gid1, g1start, g1end, intron_coord1, exon_offset1, genomic_coord1, antisense1, gname2, gid2, g2start, g2end, intron_coord2, exon_offset2, genomic_coord2, antisense2)


def map_mrna2genomic_coord(gid, mrna_coord, transcript_map):
    if gid not in transcript_map:
        return (None, None)
    (chrom, strand, transcript_coords) = transcript_map[gid]
    toffset = 0
    last_exon = 0
    eidx = 0
    #assume transcript coords are sorted
    #TODO: could speed this up using a binary search, not necessary at this time
    for (s1,e1) in transcript_coords:
        #calculate offset for the span of this current exon
        #assume 1-based
        toffset += (int(e1) - int(s1)) + 1
        if mrna_coord >= toffset:
            last_exon = eidx
        eidx += 1 
    return (last_exon, transcript_coords[last_exon])

