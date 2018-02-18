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
        #fh = gzip.open(file_,"rb")
        fh = open(file_,"rb")
        m = file_index_patt.search(file_)
        fidx = m.group(1) 
        fh_map[fidx]=[0,fh]
    return fh_map

def append_sample_counts(sample_id_offset,psamples,pcounts,samples,counts):
    return(psamples+",".join([str(int(sid)+sample_id_offset) for sid in samples.split(',')]),pcounts+counts) 
    
def main():
    samples_per_file = int(sys.argv[1])
    sorted_coords_file = sys.argv[2]
    files = sys.argv[3:]
    fhs = open_files(files)
    cfin = open(sorted_coords_file,"rb")
    (pchrm,pstrand,pstart,pend,psamples,pcounts)=(None,None,None,None,"","")
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
            if pchrm is not None:
                sys.stdout.write("\t".join([pchrm,pstrand,pstart,pend,psamples,pcounts])+"\n")
            (psamples,pcounts)=append_sample_counts((int(fID)-1)*samples_per_file,"","",samples,counts)
            (pchrm,pstrand,pstart,pend)=(chrm,strand,start,end)
        else:
            #offset the sample_per_file offset calculation by 1 so we start at 0
            (psamples,pcounts)=append_sample_counts((int(fID)-1)*samples_per_file,psamples+",",pcounts+",",samples,counts)
    if pchrm is not None:
        sys.stdout.write("\t".join([pchrm,pstrand,pstart,pend,psamples,pcounts])+"\n")
    cfin.close()
    for (fidx,f) in fhs.iteritems():
        f.close()

if __name__ == '__main__':
    main()
