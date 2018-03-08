#!/usr/bin/env python2.7
import sys
import snapconf
import os

GROUPBY_TABIX='/home/cwilks3@jhu.edu/gigatron/snaptron/scripts/groupby_tabix'
GROUPBY_GENERAL='/home/cwilks3@jhu.edu/gigatron/snaptron/scripts/groupby_general'
TABIX_MOD='/home/cwilks3@jhu.edu/samtools-1.2_mod/htslib-1.2.1/tabix'

#compilation specific, TCGA=50,GTEx=14
SPLIT_FACTOR=14
#max number of coordinate/gene names we can pass to Tabix on the command line
MAX_ENTRIES=40000

def main():
    rfile = sys.argv[1]
    compilation = sys.argv[2]
    fmap = snapconf.BASE_TABIX_DB_MAP
    rpath = snapconf.BASE_TABIX_DB_PATH
    final_map = {}
    genes2files = {}
    fin = open(rfile,"rb")
    for line in fin:
        line = line.rstrip()
        (c,s,e,g) = line.split('\t')[:4]
        c0 = '%s:%s-%s' % (c,s,e)
        #(c0,g)=line.split('\t')
        #(c,c1)=c0.split(':')
        #(s,e)=c1.split('-')
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
            if g not in genes2files:
                genes2files[g] = []
            genes2files[g].append(f)
    for (i,f) in enumerate(sorted(final_map.keys())):
        fout = None
        outpath = None
        j = 0
        k = 0
        for line in final_map[f]:
            if j % MAX_ENTRIES == 0:
                if fout is not None and not fout.closed:
                    fout.write(" | %s | tee %s.exons | %s > %s.genes 2> %s.err\n" % (GROUPBY_TABIX,outpath,GROUPBY_GENERAL,outpath,outpath))
                    fout.close()
                #TODO change i to todal number of files to be produced to round robin the access pattern
                ascii_idx = (i % SPLIT_FACTOR)+66
                outpath = "%s/%d_%d.%s" % ("/data"+str(unichr(ascii_idx)),i,k,compilation)
                fout = open("%d_%d.map.sh" % (i,k),"wb")
                fout.write('#!/bin/bash\n')
                fout.write("%s %s.bgz"% (TABIX_MOD,f))
                sys.stdout.write("/bin/bash %s_%d.map.sh\n" % (i,k))
                k+=1
            #sys.stdout.write(c+"\n"+g+"\n")
            fout.write(" "+line)
            j+=1
        if fout is not None and not fout.closed:
            fout.write(" | %s | tee %s.exons | %s > %s.genes 2> %s.err\n" % (GROUPBY_TABIX,outpath,GROUPBY_GENERAL,outpath,outpath))
            fout.close()
        #sys.stdout.write("%s -R %s.map %s.bgz | %s | tee > %s.exons | %s > %s.genes 2> %s.err\n" % (TABIX_MOD,f,f,GROUPBY_TABIX,outpath,GROUPBY_GENERAL,outpath,outpath))

if __name__ == '__main__':
    main()
