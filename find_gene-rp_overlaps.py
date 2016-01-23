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

def load_exons_and_genes(genesF):
    gtrees={}
    etrees={}
    genesIN = open(genesF)
    #map transcript (isoform) name to cluster_id ("gene")
    t_to_gene_map = {}
    #load individual transcripts (isoforms)
    for line in genesIN:
        #skip header
        if line[0] == 'c':
            continue
        line = line.rstrip()
        fields = line.split('\t')
        (cluster_id,tname,refid,strand,tstart,tend) = fields[:6]
        refid = refid.replace("chr","")
        eStarts = fields[9].split(',')
        eEnds = fields[10].split(',')
        alignID = fields[12]
        #now save the exons as intervals
        if refid not in etrees:
            etrees[refid] = IntervalTree()
        #use 1-based closed interval
        tstart=int(tstart)+1 
        for (eStart,eEnd) in zip(eStarts,eEnds):
            if len(eStart) == 0:
                continue
            #use 1-based closed interval
            eStart=int(eStart)+1
            #sys.stderr.write("%s %s %s\n"%(eStart,eEnd,cluster_id))
            #must adjust for the open intervals (both) of the interval tree
            itv = Interval(eStart-1,int(eEnd)+1, value=[cluster_id,alignID])
            etrees[refid].insert_interval(itv)
        #now map to the cluster_id and figure whether we can increase
        #the longest transcript coordinate span with these coordinates
        tend = int(tend)
        if cluster_id not in t_to_gene_map:
            t_to_gene_map[cluster_id]=[tstart,tend,refid]
        if tstart < t_to_gene_map[cluster_id][0]:
            t_to_gene_map[cluster_id][0] = tstart
        if tend > t_to_gene_map[cluster_id][1]:
            t_to_gene_map[cluster_id][1] = tend
    genesIN.close()
    #now convert the cluster (gene) coordinate extents to intervals
    for (cluster_id,span) in t_to_gene_map.iteritems():
        (st,en,refid) = span
        if refid not in gtrees:
            gtrees[refid] = IntervalTree()
        #sys.stderr.write("%d %d %s\n"%(st,en,cluster_id))
        #must adjust for the open intervals (both) of the interval tree
        itv = Interval(int(st)-1,int(en)+1,value=cluster_id)
        gtrees[refid].insert_interval(itv)
    return (etrees,gtrees)


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
        refid = refid.replace("chr","")
        orient = fields[9]
        tname = fields[10]
        gtype = fields[11]
        #use 1-based closed interval
        st=int(st)+1
        #present already in interval tree
        if "%d_%s" % (st,en) in seen:
            continue
        seen.add("%d_%s" % (st,en))
        if refid not in rtrees:
            rtrees[refid] = IntervalTree()
        #must adjust for the open intervals (both) of the interval tree
        itv = Interval(st-1,int(en)+1, value=[tname,gtype])
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
    #return ";".join(names)
 

def process_overlaps(eo,coord,ro,iline):
    (genes,genetypes) = process_overlap_values(eo)
    #genes = process_overlap_values(eo)
    (repeats,repeatclasses) = process_overlap_values(ro)
    sys.stdout.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (coord,genes,genetypes,repeats,repeatclasses,iline))


def main():
    genesF = sys.argv[1]
    #exonsF = sys.argv[2]
    repeatsF = sys.argv[2]
    intronsF = sys.argv[3]    

    (etrees,gtrees) = load_exons_and_genes(genesF)
    #etrees = load_exons(exonsF)
    rtrees = load_repeats(repeatsF)
    
    with open(intronsF,"r") as intronsIN:
        for line in intronsIN:
            fields = line.split('\t') 
            (refid,st,en,orient)=fields[1:5]
            refid = refid.replace("chr","")

            #chr/reference doesnt exist in the exon interval tree or in the repeat interval tree
            if refid not in gtrees or refid not in etrees or refid not in rtrees:
                continue
            st = int(st)
            en = int(en)
            go1 = set()
            go2 = set()
            goverlaps1 = gtrees[refid].find(st,st)
            goverlaps2 = gtrees[refid].find(en,en)
            map(lambda x: go1.add(x.value),goverlaps1)
            map(lambda x: go2.add(x.value),goverlaps2)
            cluster_ids = go1.intersection(go2)
            #only one gene must span both start and end of the intron
            #if len(cluster_ids) == 0 or len(cluster_ids) > 1:
            if len(cluster_ids) == 0:
                continue
            estarts = etrees[refid].find(st,st)
            eends = etrees[refid].find(en,en)
            #both ends are in an exon, or both are not, either way skip
            if (len(estarts) > 0 and len(eends) > 0) or (len(estarts) == 0 and len(eends) == 0): 
                continue
            #actually forget about both exons, we just need to determine that the coordinate span is within at least one gene
            #instead of filtering, we'll take any exon as along as the original span is in a gene
            #AND one end is not in an exon while the other is in an exon
            #estarts = filter_exons(estarts,cluster_ids) 
            #eends = filter_exons(eends,cluster_ids) 
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








#deprecated as we read the exons in with the genes (only from UCSC)
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
