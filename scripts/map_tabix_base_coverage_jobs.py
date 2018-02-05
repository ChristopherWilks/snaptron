#!/usr/bin/env python2.7
import sys
import snapconf
import os

GROUPBY_TABIX='/home/cwilks3@jhu.edu/gigatron/snaptron/scripts/groupby_tabix'
GROUPBY_GENERAL='/home/cwilks3@jhu.edu/gigatron/snaptron/scripts/groupby_general'
TABIX_MOD='/home/cwilks3@jhu.edu/samtools-1.2_mod/htslib-1.2.1/tabix'

def main():
    rfile = sys.argv[1]
    fmap = snapconf.BASE_TABIX_DB_MAP
    rpath = snapconf.BASE_TABIX_DB_PATH
    final_map = {}
    fin = open(rfile,"rb")
    for line in fin:
        line = line.rstrip()
        (c0,g)=line.split('\t')
        (c,c1)=c0.split(':')
        (s,e)=c1.split('-')
        files = []
        regions = fmap[c]
        for region in regions:
            (f,s2,e2)=region[:]
            if int(s) >= int(s2) and int(e) <= int(e2):
                files.append(os.path.join(rpath,f))
            elif int(s) <= e2 and int(e) >= s2:
                sys.stderr.write("SPLIT\t%s\n" % line)
        for f in files:
            if f not in final_map:
                final_map[f]=[]
            final_map[f].append(c0+" "+g)
    for (i,f) in enumerate(sorted(final_map.keys())):
        ascii_idx = (i % 14)+66
        outpath = "%s/%d.tcga" % ("/data"+str(unichr(ascii_idx)),i)
        with open("%s.map.sh" % f,"wb") as fout:
            fout.write('#!/bin/bash\n')
            fout.write("%s %s.bgz"% (TABIX_MOD,f))
            for line in final_map[f]:
                #sys.stdout.write(c+"\n"+g+"\n")
                fout.write(" "+line)
            fout.write(" | %s | tee %s.exons | %s > %s.genes 2> %s.err\n" % (GROUPBY_TABIX,outpath,GROUPBY_GENERAL,outpath,outpath))
        sys.stdout.write("/bin/bash %s.map.sh\n" % f)
        #sys.stdout.write("%s -R %s.map %s.bgz | %s | tee > %s.exons | %s > %s.genes 2> %s.err\n" % (TABIX_MOD,f,f,GROUPBY_TABIX,outpath,GROUPBY_GENERAL,outpath,outpath))

if __name__ == '__main__':
    main()
