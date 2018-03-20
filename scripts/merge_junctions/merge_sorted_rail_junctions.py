#!/bin/env python2.7
#merge multi-Rail-run junctions into one junction table
#this assumes each subrun numbers it's samples from 0-# samples
#this script will renumber them by the part # of the run file
import sys
import re
import gzip


file_index_patt = re.compile(r'(\d\d)')
def open_files(files):
    fh_map = {}
    for file_ in files:
        fh = open(file_,"rb")
        m = file_index_patt.search(file_)
        fidx = m.group(1) 
        fh_map[fidx]=[0,fh]
    return fh_map

def order_samples_and_counts(all_samples, all_counts):
    both = sorted([[int(x), all_counts[i]] for (i,x) in enumerate(all_samples)],key=lambda k: k[0])
    return (','.join([str(x[0]) for x in both]), ','.join([x[1] for x in both]))

def append_sample_counts(sample_id_offset,psamples,pcounts,samples,counts,fID,fID2sample,sample_map):
    sample_ids = []
    new_counts = []
    counts = counts.split(',')
    out_of_order = False
    for (i,sid) in enumerate(samples.split(',')):
        k = "%s.%s" % (fID,sid)
        (srp,srr) = fID2sample[k]
        new_id = int(sid) + sample_id_offset
        #in case of duplicates but where junctions may still be only in one of the duplicates
        #we have to track the correct sample_id
        if srr in sample_map:
            new_id = sample_map[srr]
            out_of_order = True
        sample_ids.append(str(new_id))
        new_counts.append(counts[i])
        sample_map[srr]=new_id
    if len(pcounts) > 0 and len(sample_ids) > 0:
        psamples += "," 
        pcounts += ","
    (all_samples, all_counts) = (psamples+",".join(sample_ids), pcounts+",".join(new_counts))
    #keep samples in sorted order by sample_id
    if out_of_order:
        return order_samples_and_counts(all_samples.split(','), all_counts.split(','))
    return(all_samples, all_counts) 
  
 
def load_samples(samples_file):
    fID2sample = {}
    fIDcounts = {}
    srrs = set()
    count = 0
    pfID = None
    with open(samples_file,"rb") as fin:
        for line in fin:
            #fID ~ 01, lID ~ 5 (starts at 0), study_sample ~ SRP-SRR
            (fID,lID,study_sample) = line.rstrip().split('\t')
            if pfID is not None and pfID != fID:
                fIDcounts[fID]=count
                count = 0
            (study,sample) = study_sample.split('-')
            pfID = fID
            srrs.add(sample)
            fID2sample['%s.%s' % (fID,lID)]=[study,sample]
            count += 1 
        if pfID is not None:
            fIDcounts[fID]=count
    return (fID2sample, fIDcounts)  
    
 
def main():
    samples_per_file = int(sys.argv[1])
    sorted_coords_file = sys.argv[2]
    (fID2sample, fIDcounts) = load_samples(sys.argv[3])
    files = sys.argv[4:]
    fhs = open_files(files)
    cfin = open(sorted_coords_file,"rb")
    (pchrm,pstrand,pstart,pend,psamples,pcounts)=(None,None,None,None,"","")
    sample_map = {}
    for line in cfin:
        line = line.rstrip()
        (fID_,chrm,start,end)=line.split('\t')
        (fID,lineID)=fID_.split('.')
        lineID=int(lineID)
        (fidx,fh) = fhs[fID]
        if fidx != lineID:
            raise Exception("file %s out of sync %d %d\n" % (fID,lineID,fidx))
        (chrm,strand,start,end,samples,counts)=fh.readline().rstrip().split('\t')
        fhs[fID][0]+=1
        if pchrm != chrm or pstart != start or pend != end:
            if pchrm is not None and len(psamples) > 0:
                sys.stdout.write("\t".join([pchrm,pstrand,pstart,pend,psamples,pcounts])+"\n")
            (psamples,pcounts)=append_sample_counts((int(fID)-1)*samples_per_file,"","",samples,counts,fID,fID2sample,sample_map)
            (pchrm,pstrand,pstart,pend)=(chrm,strand,start,end)
        else:
            #offset the sample_per_file offset calculation by 1 so we start at 0
            (psamples,pcounts)=append_sample_counts((int(fID)-1)*samples_per_file,psamples,pcounts,samples,counts,fID,fID2sample,sample_map)
    if pchrm is not None and len(psamples) > 0:
        sys.stdout.write("\t".join([pchrm,pstrand,pstart,pend,psamples,pcounts])+"\n")
    cfin.close()
    for srr in sample_map.keys():
        sys.stderr.write("%s\t%s\n" % (sample_map[srr],srr))

if __name__ == '__main__':
    main()
