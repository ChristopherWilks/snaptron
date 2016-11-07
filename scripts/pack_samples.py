#!/usr/bin/env python2.7
import sys
import multiprocessing
import snaputil as su
from bitarray import bitarray
MAX_ID=81066375

path='/data3/snaptron/sample_ids_full'
nthreads_total=8

def pack_sample_mapped_ids(line):    
    (sid,ids) = line.rstrip().split("|")
    ba=bitarray()
    i = 0
    last_y = -1
    ids_ = ids.split(",")
    ids_.pop()
    for y in sorted([int(x) for x in ids_]):
        last_y = y
        while i < y:
            ba.append(False)
            i+=1
        ba.append(True)
        i+=1
    while i <= MAX_ID:
        ba.append(False)
        i+=1
    #su.store_cpickle_file("./sample_ids1_%s.pkl" % (k),ba, compress=True)
    su.store_cpickle_file("%s/%s.pkl" % (path,sid), ba, compress=False)
    return True


batch = []
count = 0
for line in sys.stdin:
    batch.append(line)
    count+=1
    if len(batch) == 8:
        pool = multiprocessing.Pool(processes=nthreads_total)
        done = pool.map(pack_sample_mapped_ids, batch)
        pool.close()
        pool.join()
        del batch[:]
    print "finished mapping @ %d" % count

if len(batch) > 0:
    pool = multiprocessing.Pool(processes=len(batch))
    pool.map(pack_sample_mapped_ids, batch)


