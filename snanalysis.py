#!/usr/bin/env python2.7
'''
Takes a list of snaptron_ids, a function, and a rank ordering
Returns list of samples ranked by function run and prented according to ordering
'''

import sys
import os
import subprocess
import json
import time
import operator

import gzip

import snapconf
import snaputil
import snaptron

import sqlite3
sconn = sqlite3.connect(snapconf.SNAPTRON_SQLITE_DB)
sc = sconn.cursor()

DEBUG_MODE=False

def create_junction_grouping_by_sample(introns,samples_group):
    #for (tid,samples) in introns.iteritems():
        #(sids_,coverages_) = samples
    for (tid,samples,coverages_) in introns:
        sids = samples.split(',')
        coverages = coverages_.split(',')
        for (i,sid) in enumerate(sids):
            cov = int(coverages[i])
            if sid not in samples_group:
                samples_group[sid]=[0,0]
            samples_group[sid][0]+=1 
            samples_group[sid][1]+=cov 

def get_samples_for_snaptron_ids(ids):
    select = 'SELECT snaptron_id,samples,read_coverage_by_sample FROM intron where snaptron_id in'
    results = snaputil.retrieve_from_db_by_ids(sc,select,ids)
    return results
    #intron2samples={}
    #for (tid,samples,covs) in snaputil.retrieve_from_db_by_ids(sc,select,ids):
    #    intron2samples[tid]=[samples,covs]
    #return intron2samples 
        
def junction_inclusion_ratio(params):
    ids_a = params['ids_a']
    ids_b = params['ids_b']
    ratio_type = params['ratio']
    
    #loop through ids, get the ids2samples(sid,coverage) and then compute the ratio for each sample
    #1) retrieve list of all samples and their coverage for each snaptron id (track these via sets and hashes)
    sids_a = set()
    coverages_a = {}
    sids_b = set()
    coverages_b = {}
    introns2samples_a = get_samples_for_snaptron_ids(ids_a)
    introns2samples_b = get_samples_for_snaptron_ids(ids_b)

    samples_a = {}
    create_junction_grouping_by_sample(introns2samples_a,samples_a)
    samples_b = {}
    create_junction_grouping_by_sample(introns2samples_b,samples_b)

    #2) find ratio of sample sets (either counts or coverages)
    sample_ratios={}
    sids = set(samples_a.keys()).union(set(samples_b.keys()))
    for sid in sids:
        a_cnt = 0
        a_cov = 0
        b_cnt = 0
        b_cov = 0
        if sid in samples_a:
            a_cnt=samples_a[sid][0]
            a_cov=samples_a[sid][1]
        if sid in samples_b:
            b_cnt=samples_b[sid][0]
            b_cov=samples_b[sid][1]
        val_a = a_cnt
        val_b = b_cnt
        if ratio_type == 'cov':
            val_a = a_cov 
            val_b = b_cov 
        sample_ratios[sid]=[((val_b - val_a)/(val_b+val_a)),val_a,val_b]
    return sample_ratios

def sorted_cmp_by_array_val(a,b):
    return cmp(a[1][0],b[1][0])

#ORDERINGS={'desc':'descending_all','T':'top_x','B':'bottom_x','asc':'ascending_all')
def sort_sample_ratios(sample_ratios,order,stream_back=True):
    reverse = True
    limit = None
    order_=order.split(':')
    order = order_[0]
    if len(order_) > 1:
        limit = int(order_[1])
    if order == 'asc' or order == 'B':
        reverse = False
    counter = 0
    for sid in sorted(sample_ratios.items(),cmp=sorted_cmp_by_array_val,reverse=reverse):
        (sid,vals) = sid
        (ratio,val_a,val_b) = vals
        if not limit or limit > counter:
            sys.stdout.write("%s\t%s\t%s\t%s\n" % (sid,ratio,val_a,val_b)) 
            counter+=1

def process_params(input_):
    params = {'ids_a':[],'ids_b':[],'compute':"",'order':"desc",'ratio':'cnt'}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            sys.stderr.write("unknown parameter %s, exiting\n" % param)
            sys.exit(-1)
        if key[:3] == 'ids':
            params[key]=val.split(',')
        else:
            params[key]=val
    return params
   
compute_functions = {'jir':junction_inclusion_ratio} 
def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    params = process_params(input_)
    compute_func = compute_functions[params['compute']]
    sample_ratios = compute_func(params)
    order = params['order']
    sort_sample_ratios(sample_ratios,order)


if __name__ == '__main__':
    main()
