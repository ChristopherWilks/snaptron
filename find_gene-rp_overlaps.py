#!/usr/bin/env python2.7

import sys
import re
from bx.intervals.intersection import Interval
#from bx.intervals.intersection import IntervalNode
from bx.intervals.intersection import IntervalTree

#itree per chromosome create interval tree
#itree[rp.refid] = IntervalTree()
#iv = Interval(rp.ref_i, rp.ref_f, value=rp.rep_cl)
#itree[rp.refid].insert_interval(iv)
#itree find
#for olap in itree[refid].find(ref_i, ref_f):

def load_exons(exonsF):
    etrees={}
    typePattern = re.compile(r' gene_(bio)?type "([^"]+)"')
    tnamePattern = re.compile(r' transcript_name "([^"]+)"')
    gnamePattern = re.compile(r' gene_name "([^"]+)"')
    gtype = ""
    tname = ""
    seen = set()
    exonsIN = open(exonsF)
    for line in exonsIN:
        line = line.rstrip()
        fields = line.split('\t')
        (refid,source,type,st,en) = fields[:5]
        orient = fields[6]
        rest = fields[8]
        m = typePattern.search(rest)
        if m:
            gtype = m.group(2)
        m = tnamePattern.search(rest)
        if m:
            tname = m.group(1)
        else:
            m = gnamePattern.search(rest)
            if m:
                tname = m.group(1)

        #present already in interval tree
        if "%s_%s" % (st,en) in seen:
            continue
        seen.add("%s_%s" % (st,en))
        if refid not in etrees:
            etrees[refid] = IntervalTree()
        itv = Interval(int(st),int(en), value=[tname,gtype])
        etrees[refid].insert_interval(itv)
    exonsIN.close()
    return etrees

def load_repeats(repeatsF):
    rtrees={}
    gtype = ""
    tname = ""
    seen = set()
    repeatsIN = open(repeatsF)
    FIRST = True
    for line in repeatsIN:
        #skip header
        if FIRST:
            FIRST = False
            continue
        line = line.rstrip()
        fields = line.split('\t')
        (refid,st,en) = fields[5:8]
        orient = fields[9]
        tname = fields[10]
        gtype = fields[11]

        #present already in interval tree
        if "%s_%s" % (st,en) in seen:
            continue
        seen.add("%s_%s" % (st,en))
        if refid not in rtrees:
            rtrees[refid] = IntervalTree()
        itv = Interval(int(st),int(en), value=[tname,gtype])
        rtrees[refid].insert_interval(itv)
    repeatsIN.close()
    return rtrees

def process_overlap_values(overlaps):
    names = []
    types = []
    for overlap in overlaps:
        names.append(overlap.value[0]) 
        types.append(overlap.value[1]) 
    return (";".join(names),";".join(types))
 

def process_overlaps(eo,coord,ro,iline):
    (genes,genetypes) = process_overlap_values(eo)
    (repeats,repeatclasses) = process_overlap_values(ro)
    sys.stdout.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (coord,genes,genetypes,repeats,repeatclasses,iline))


def main():
    exonsF = sys.argv[1]
    repeatsF = sys.argv[2]
    intronsF = sys.argv[3]    

    etrees = load_exons(exonsF)
    rtrees = load_repeats(repeatsF)
    
    with open(intronsF,"r") as intronsIN:
        for line in intronsIN:
            fields = line.split('\t') 
            (refid,st,en,orient)=fields[1:5]
            refid = refid.replace("chr","")
            #chr/reference doesnt exist in the exon interval tree or in the repeat interval tree
            if refid not in etrees or refid not in rtrees:
                continue
            st = int(st)
            en = int(en)
            estarts = etrees[refid].find(st,st)
            eends = etrees[refid].find(en,en)
            #both ends are in an exon, or both are not, either way skip
            if (len(estarts) > 0 and len(eends) > 0) or (len(estarts) == 0 and len(eends) == 0): 
                continue
            #default to start as the repeat overlapping end
            eoverlaps = eends
            coord = st
            if len(eends) == 0:
                eoverlaps = estarts
                coord = en
            #check for overlaps in the repeats via chosen coordinate
            roverlaps = rtrees[refid].find(coord,coord) 
            #if no repeat overlaps skip
            if len(roverlaps) == 0:
                continue
            process_overlaps(eoverlaps,coord,roverlaps,line) 


if __name__ == '__main__':
    main()
