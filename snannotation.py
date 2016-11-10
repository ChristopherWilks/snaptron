#!/usr/bin/env python2.7
'''
Similar to the main Snaptron service, takes coordinate range or gene name
and returns list of transcript exons
'''

import sys
import os
import subprocess
import json
import time
import operator
import re

import gzip

import snapconf
import snaputil
import snaptron

DEBUG_MODE=False

def process_params(input_):
    params = {'regions':[],'contains':'0','within':'0','exact':'0','limit':20}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            sys.stderr.write("unknown parameter %s, exiting\n" % param)
            sys.exit(-1)
        if key == 'regions':
            subparams = val.split(',')
            for subparam in subparams:
                params[key].append(subparam)
        else:
            params[key]=val
    return params


def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    params = process_params(input_)
    snaptron.query_gene_regions(params['regions'],contains=bool(int(params['contains'])),within=(int(params['within'])),exact=bool(int(params['exact'])),limit=int(params['limit']))

if __name__ == '__main__':
    main()
