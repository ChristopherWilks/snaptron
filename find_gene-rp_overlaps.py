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
    
by_sample_counts = {}

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
            itv = Interval(eStart-1,int(eEnd)+1, value=[cluster_id,alignID,strand])
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
        strand = fields[9]
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
        itv = Interval(st-1,int(en)+1, value=[tname,gtype,strand])
        rtrees[refid].insert_interval(itv)
    repeatsIN.close()
    return rtrees

def process_overlap_values(overlaps,strand):
    names = []
    types = []
    strands = []
    overlap_counts = 0
    same_sense_overlap_counts = 0
    for overlap in overlaps:
        names.append(overlap.value[0]) 
        types.append(overlap.value[1]) 
        strands.append(overlap.value[2]) 
        overlap_counts=1 
        if overlap.value[2] == strand:
            same_sense_overlap_counts=1
    return (overlap_counts,same_sense_overlap_counts,";".join(names),";".join(types),";".join(strands))
 

def process_overlaps(eo,coord,ro,strand,samples,cov,iline):
    (g_counts,g_sense_counts,genes,genetypes,gstrands) = process_overlap_values(eo,strand)
    (r_counts,r_sense_counts,repeats,repeatclasses,rstrands) = process_overlap_values(ro,strand)
    sense_matches = (g_sense_counts == r_sense_counts == 1)
    for (i,sample) in enumerate(samples):
        #already know that we have a REL, check to see if we hav a matching sense REL
        if sample not in by_sample_counts:
            #count,sense_matches?,coverage
            by_sample_counts[sample]=[0,0,0]
        by_sample_counts[sample][0]+=1
        by_sample_counts[sample][1]+=int(sense_matches)
        by_sample_counts[sample][2]+=cov[i]
    sys.stdout.write("%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (coord,genes,genetypes,gstrands,repeats,repeatclasses,rstrands,sense_matches,iline))

def load_samples(samplesF):
    samplesIN = open(samplesF)
    samples={}
    for line in samplesIN:
        (sample_id,count,cov) = line.rstrip().split('\t')
        samples[sample_id]=[count,cov]
    samplesIN.close()
    return samples

def main():
    genesF = sys.argv[1]
    #exonsF = sys.argv[2]
    repeatsF = sys.argv[2]
    intronsF = sys.argv[3]
    samplesF = sys.argv[4]

    (etrees,gtrees) = load_exons_and_genes(genesF)
    #etrees = load_exons(exonsF)
    rtrees = load_repeats(repeatsF)
    
    #load file of sample2[count,coverage] mapping
    sample2stats = load_samples(samplesF)

    #track junction counts by sample
    #index 0 = total REL junctions
    #index 1 = total REL junctions matching sense
    
    with open(intronsF,"r") as intronsIN:
        for line in intronsIN:
            fields = line.split('\t') 
            (refid,st,en,ilen,strand)=fields[1:6]
            samples = fields[11].split(',')
            refid = refid.replace("chr","")
            cov = fields[12].split(',')

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
            process_overlaps(eoverlaps,coord,roverlaps,strand,samples,cov,line) 

    with open("sample_counts.tsv","w") as f:
        for (sample,counts) in by_sample_counts.iteritems():
            (rel_counts,rel_sense_counts,rel_cov) = counts
            (total_intron_counts,total_intron_cov) = sample2stats[sample]
            f.write("%s\t%s/%s\t%s/%s\t%s/%s\n" % (str(sample),str(rel_sense_counts),str(rel_counts),str(rel_counts),str(total_intron_counts),str(rel_cov),str(total_intron_cov)))


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
        strand = fields[6]
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
