#!/usr/bin/env python2.7
import sys
import snaputil as su
from bitarray import bitarray
MAX_ID=81063662

COMPRESSED=False
path='/data3/snaptron/sample_ids_full'
#path='/data3/snaptron/sample_ids'
#suffix='.gz'
suffix=''

def orthem(ba1,ba2):
    ba_final = ba1 | ba2
    return ba_final

def setthem(ba_final):
    i = 0
    s1=set()
    [s1.add(i) for (i,x) in enumerate(ba_final) if x]
    #for bit in ba_final:
    #    if bit:
    #        s1.add(i)
    #    i+=1
    return s1

ba_final = su.load_cpickle_file("%s/0.pkl%s" % (path,suffix), compressed=COMPRESSED)
for i in xrange(1,5000):
    ba2 = su.load_cpickle_file("%s/%s.pkl%s" % (path,str(i),suffix), compressed=COMPRESSED)
    if ba2 != None:
        ba_final = orthem(ba2,ba_final)

s1 = setthem(ba_final)
print len(s1)
#sys.stdout.write(",".join([str(x) for x in s1]))
