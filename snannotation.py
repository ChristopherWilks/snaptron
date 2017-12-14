#!/usr/bin/env python2.7

# Copyright 2016, Christopher Wilks <broadsword@gmail.com>
#
# This file is part of Snaptron.
#
# Snaptron is free software: you can redistribute it and/or modify
# it under the terms of the 
# Creative Commons Attribution-NonCommercial 4.0 
# International Public License ("CC BY-NC 4.0").
#
# Snaptron is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# CC BY-NC 4.0 license for more details.
#
# You should have received a copy of the CC BY-NC 4.0 license
# along with Snaptron.  If not, see 
# <https://creativecommons.org/licenses/by-nc/4.0/legalcode>.

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
import urllib

import gzip

#do this to avoid full paths to python scripts in tracebacks, for security
if sys.path[0] != './':
    sys.path=['./'] + sys.path

import snapconf
import snapconfshared
import snaputil
import snaptron
import snquery

DEBUG_MODE=False

def process_params(input_):
    params = {'regions':[],'contains':'0','either':'0','exact':'0','limit':20}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            snaputil.log_error(param, "query parameter, exiting")
            sys.exit(-1)
        if key == 'regions':
            subparams = val.split(',')
            for subparam in subparams:
                params[key].append(subparam)
        else:
            params[key]=val
    return params


class GeneCoords(object):

    def __init__(self,load_refseq=True,load_canonical=True,load_transcript=False):
        self.ensembl_id_patt = re.compile('(ENST\d+)')
        #this is the main gene2coordinate map we use for servicing HUGO gene symbol queries (RefSeq)
        if load_refseq:
            gene_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.REFSEQ_ANNOTATION)
            gencode_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconfshared.GENCODE_ANNOTATION)
            gene_pickle_file = "%s/refseq_gencode.pkl" % snapconf.TABIX_DB_PATH
            self.gene_map = snaputil.load_cpickle_file(gene_pickle_file)
            if not self.gene_map:
                self.load_gene_coords(gene_file)
                #add additional annotations (w/ different gene names)
                self.extend_gene_coords(gencode_file)
            snaputil.store_cpickle_file(gene_pickle_file,self.gene_map)
        if load_canonical:
            canonical_gene_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.CANONICAL_ANNOTATION)
            canonical_gene_pickle_file = "%s.pkl" % (canonical_gene_file)
            self.canonical_gene_map = snaputil.load_cpickle_file(canonical_gene_pickle_file)
            if not self.canonical_gene_map:
                self.load_canonical_gene_coords(canonical_gene_file)
            snaputil.store_cpickle_file(canonical_gene_pickle_file,self.canonical_gene_map)
       
        #per transcript exons
        if load_transcript:
            transcript_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.TABIX_GENE_INTERVAL_DB)
            transcript_pickle_file = "%s.pkl" % (transcript_file)
            self.transcript_map = snaputil.load_cpickle_file(transcript_pickle_file)
            if not self.transcript_map:
                self.load_transcripts(transcript_file)
            snaputil.store_cpickle_file(transcript_pickle_file,self.transcript_map)

    def extend_gene_coords(self, gencode_file):
        with gzip.open(gencode_file,"r") as f:
            #chr1    HAVANA  gene    11869   14409   .       +       .       ID=ENSG00000223972.5;gene_id=ENSG00000223972.5;gene_type=transcribed_unprocessed_pseudogene;gene_status=KNOWN;gene_name=DDX11L1;level=2;havana_gene=OTTHUMG00000000961.2
            for line in f:
                if line[0] == '#':
                    continue
                fields = line.rstrip().split('\t')
                if fields[2] != 'gene':
                    continue
                (chrom,st,en) = (fields[0],int(fields[3]),int(fields[4]))
                subfields=dict([x.split('=') for x in fields[8].split(';')])
                self.gene_map[subfields['gene_id'].upper()]={chrom:[[st,en]]}

    def load_gene_coords(self,filepath):
        gene_map = {}
        with open(filepath,"r") as f:
            for line in f:
                fields = line.rstrip().split('\t')
                (gene_name,chrom,st,en) = (fields[0].upper(),fields[2],int(fields[4]),int(fields[5]))
                #UCSC OFFSET
                st += 1
                if not snapconf.CHROM_PATTERN.search(chrom):
                    continue
                if gene_name in gene_map:
                    add_tuple = True
                    if chrom in gene_map[gene_name]:
                        for (idx,gene_tuple) in enumerate(gene_map[gene_name][chrom]):
                            (st2,en2) = gene_tuple
                            if (st2 <= en and en2 >= en) or (st <= en2 and en >= en2) or abs(en2-en) <= snapconf.MAX_GENE_PROXIMITY:
                                add_tuple = False
                                if st < st2:
                                    gene_map[gene_name][chrom][idx][0] = st
                                if en > en2:
                                    gene_map[gene_name][chrom][idx][1] = en
                    #add onto current set of coordinates
                    if add_tuple:
                        if chrom not in gene_map[gene_name]:
                            gene_map[gene_name][chrom]=[]
                        gene_map[gene_name][chrom].append([st,en]) 
                else:
                    gene_map[gene_name]={}
                    gene_map[gene_name][chrom]=[[st,en]]
        self.gene_map = gene_map
        return gene_map
    
    def load_canonical_gene_coords(self,filepath):
        gene_map = {}
        with open(filepath,"r") as f:
            for line in f:
                fields = line.rstrip().split('\t')
                (kg_id,cluster_id,bin_,refgname,chrom,strand,tstart,tend,cstart,cend,ecount,estarts_,eends_,score,gene_name) = fields[:15]
                gene_name = gene_name.upper()
                estarts = estarts_.split(',')[:-1]
                eends = eends_.split(',')[:-1]
                #if we're not on an autosome/sex chromosom OR there's no splice sites, skip
                if not snapconf.CHROM_PATTERN.search(chrom) or len(estarts) < 2:
                    continue
                #shift to get introns
                temp = estarts[1:]
                estarts = eends[:-1]
                eends = temp
                #need to offset by +1 AND drop the last item, since UCSC has a trailing comma
                if strand == '-':
                    line_map = [[int(x1)+1,int(x2)] for (x1,x2) in zip(reversed(estarts),reversed(eends))] 
                else:
                    line_map = [[int(x1)+1,int(x2)] for (x1,x2) in zip(estarts,eends)] 
                gene_map[gene_name]=[chrom,strand,line_map]
        self.canonical_gene_map = gene_map
        return gene_map

    def load_transcripts(self,filepath):
        gene_map = {}
        with gzip.open(filepath,"r") as f:
            for line in f:
                #chr1    GC,ES   transcript      26504039        26516377        .       +       .       transcript_id "ENST00000361530.6,ENST00000361530";cds_span "26504039-26516036";exons "26503894-26504090,26506944-26507101";
                (chrom,annots,ttype,tstart,tend,_,strand,_,info) = line.rstrip().split('\t')
                fields = info.split(';')
                m = self.ensembl_id_patt.search(fields[0])
                if m is None:
                    continue
                eid = m.group(1)
                fields[2] = fields[2].replace('"','')
                (_,exons) = fields[2].split(' ')
                exons = exons.split(',')
                if strand == '-':
                    exons.reverse()
                exon_coords = [x.split('-') for x in exons]
                gene_map[eid]=[chrom,strand,exon_coords]
        self.transcript_map = gene_map
        return gene_map
                    

    def gene2coords(self,geneq):
        exon_idxs = []
        if ":" in geneq:
            (geneq,exon_idxs_) = geneq.split(":")
            exon_idxs = exon_idxs_.split(';')
        geneq = geneq.upper()
        if (len(exon_idxs) == 0 and geneq not in self.gene_map) or (len(exon_idxs) > 0 and geneq not in self.canonical_gene_map):
            snaputil.log_error(geneq, "gene name, exiting")
            sys.exit(-1)
        if len(exon_idxs) > 0:
            chrom = self.canonical_gene_map[geneq][0]
            strand = self.canonical_gene_map[geneq][1]
            regions = []
            for eidx in exon_idxs:
                if '-' in eidx:
                    (e1,e2) = eidx.split('-')
                    for eidx2 in xrange(int(e1),int(e2)+1):
                        (start,end) = self.canonical_gene_map[geneq][2][int(eidx2)-1]
                        regions.append([start,end])
                else:        
                    (start,end) = self.canonical_gene_map[geneq][2][int(eidx)-1]
                    regions.append([start,end])
            return sorted({chrom:regions}.iteritems())
        return sorted(self.gene_map[geneq].iteritems())


def query_gene_regions(intervalq,contains=False,either=0,exact=False,limit=20):
    print_header = True
    ra = snaptron.default_region_args._replace(tabix_db_file=snapconf.TABIX_GENE_INTERVAL_DB,range_filters=None,save_introns=False,header=snapconf.GENE_ANNOTATION_HEADER,prefix="Mixed:G",cut_start_col=1,region_start_col=snapconf.GENE_START_COL,region_end_col=snapconf.GENE_END_COL,contains=contains,either=either,exact=exact,debug=DEBUG_MODE)
    gc = GeneCoords()
    limit_filter = 'perl -ne \'chomp; @f=split(/\\t/,$_); @f1=split(/;/,$f[8]); $boost=0; $boost=100000 if($f1[1]!~/"NA"/); @f2=split(/,/,$f1[2]); $s1=$f1[2]; $f[5]=(scalar @f2)+$boost; print "".(join("\\t",@f))."\\n";\' | sort -t"	" -k6,6nr'
    additional_cmd = ""
    ra_additional_cmd = ra
    if limit > 0:
        sys.stderr.write("limit_filter %s\n" % (urllib.quote(limit_filter)))
        additional_cmd = "%s | head -%d" % (limit_filter,limit)
        ra_additional_cmd = ra._replace(additional_cmd=additional_cmd)
    for interval in intervalq:
        if snapconf.INTERVAL_PATTERN.search(interval):
           runner = snquery.RunExternalQueryEngine(snapconf.TABIX,interval,None,set(),region_args=ra)
           (ids,sids) = runner.run_query()
        else:
            intervals = gc.gene2coords(interval)
            sys.stderr.write("# of gene intervals: %d\n" % (len(intervals)))
            #if given a gene name, first convert to coordinates and then search tabix
            for (chrom,coord_tuples) in intervals:
                sys.stderr.write("# of gene intervals in chrom %s: %d\n" % (chrom,len(coord_tuples)))
                for coord_tuple in coord_tuples:
                    (st,en) = coord_tuple
                    runner = snquery.RunExternalQueryEngine(snapconf.TABIX,"%s:%d-%d" % (chrom,st,en),None,set(),region_args=ra_additional_cmd)
                    (ids,sids_) = runner.run_query()
                    if ra_additional_cmd.print_header:
                        ra_additional_cmd=ra_additional_cmd._replace(print_header=False)
  
def main():
    global DEBUG_MODE
    input_ = sys.argv[1]
    if len(sys.argv) > 2:
       DEBUG_MODE=True
    params = process_params(input_)
    query_gene_regions(params['regions'],contains=bool(int(params['contains'])),either=(int(params['either'])),exact=bool(int(params['exact'])),limit=int(params['limit']))

if __name__ == '__main__':
    main()
