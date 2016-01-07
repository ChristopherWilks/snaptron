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
        if line[0]=='#':
            continue
        fields = line.split('\t')
        (refid,source,type_,st,en) = fields[:5]
        refid = refid.replace(r'^chr','')
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

def process_overlap_values(overlaps,type_):
    lables = []
    names = []
    types = []
    for overlap in overlaps:
        lables.append(type_)
        names.append(overlap.value[0]) 
        types.append(overlap.value[1]) 
    return (";".join(lables),";".join(names),";".join(types))
 

def process_overlaps(eo,uo,rgo,ro,iline):

    (elables,egenes,egenetypes) = process_overlap_values(eo,'ES')
    (ulables,ugenes,ugenetypes) = process_overlap_values(eo,'UC')
    (rglables,rggenes,rggenetypes) = process_overlap_values(eo,'RG')
    (rlables,repeats,repeatclasses) = process_overlap_values(ro,'RP')
    #sys.stdout.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (coord,genes,genetypes,repeats,repeatclasses,iline))
    lables = ";".join([elables,ulables,rglables,rlables])
    features = ";".join([egenes,ugenes,rggenes,repeats])
    ftypes = ";".join([egenetypes,ugenetypes,rggenetypes,repeatclasses]) 
    sys.stdout.write("%s\t%s\t%s\t%s\n" % (iline,lables,features,ftypes))


def main():
    es_exonsF = sys.argv[1]
    uc_exonsF = sys.argv[2]
    rg_exonsF = sys.argv[3]
    repeatsF = sys.argv[4]
    intronsF = sys.argv[5]    

    es_etrees = load_exons(es_exonsF)
    uc_etrees = load_exons(uc_exonsF)
    rg_etrees = load_exons(rg_exonsF)
    rtrees = load_repeats(repeatsF)

    #sys.stdout.write("gigatron_id\tchromosome\tstart\tend\tstrand\tdonor\tacceptor\tsamples\tread_coverage_by_sample\tsamples_count\tcoverage_count\tcoverage_sum\tcoverage_avg\tcoverage_median\toverlapped_features\toverlapped_feature_sources\toverlapped_feature_types\n")
    sys.stdout.write('\t'.join(["gigatron_id","chromosome","start","end","length","strand","annotated?","left_motif","right_motif","left_annotated?","right_annotated?","samples","read_coverage_by_sample","samples_count","coverage_sum","coverage_avg","coverage_median","overlapped_features","overlapped_feature_sources","overlapped_feature_types","\n"]))
#\trepeats_overlapped\trepeat_classes\n")
    with open(intronsF,"r") as intronsIN:
        for line in intronsIN:
            fields = line.split('\t') 
            (refid,st,en,length,orient)=fields[1:6]
            refid = refid.replace("chr","")
            #chr/reference doesnt exist in the exon interval tree or in the repeat interval tree
            st = int(st)
            en = int(en)
            eoverlaps=[]
            uoverlaps=[]
            rgoverlaps=[]
            roverlaps=[]
            if refid in es_etrees:
                eoverlaps = es_etrees[refid].find(st,en)
            if refid in uc_etrees:
                uoverlaps = uc_etrees[refid].find(st,en)
            if refid in rg_etrees:
                rgoverlaps = rg_etrees[refid].find(st,en)
            #check for overlaps in the repeats via chosen coordinate
            if refid in rtrees:
                roverlaps = rtrees[refid].find(st,en) 
            #if no repeat overlaps skip
            process_overlaps(eoverlaps,uoverlaps,rgoverlaps,roverlaps,line) 


if __name__ == '__main__':
    main()
