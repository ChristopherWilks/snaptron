#!/usr/bin/env python
import sys
import os
import cPickle
import gzip
from collections import namedtuple
import re
import urllib
import urllib2
import json

import snapconf

REQ_FIELDS=[]

RegionArgs = namedtuple('RegionArgs','tabix_db_file range_filters intron_filter sample_filter save_introns save_samples stream_back print_header header prefix cut_start_col region_start_col region_end_col contains within exact result_count return_format score_by post original_input_string coordinate_string sample_fields debug')

default_region_args = RegionArgs(tabix_db_file=snapconf.TABIX_INTERVAL_DB, range_filters=[], intron_filter=None, sample_filter=None, save_introns=False, save_samples=False, stream_back=True, print_header=True, header="DataSource:Type\t%s" % snapconf.INTRON_HEADER, prefix="%s:I" % snapconf.DATA_SOURCE, cut_start_col=snapconf.CUT_START_COL, region_start_col=snapconf.INTERVAL_START_COL, region_end_col=snapconf.INTERVAL_END_COL, contains=False, within=0, exact=False, result_count=False, return_format=snapconf.TSV, score_by="samples_count", post=False, original_input_string='', coordinate_string='', sample_fields=[], debug=True)

def parse_json_query(clause,region_args=default_region_args):
    sys.stderr.write("clause %s\n"  % (clause))
    ra = region_args
    #legacy_remap = {'gene':'genes','interval':'intervals','metadata_keyword':'metadata_keywords'}
    legacy_remap = {}
    fields={}
    fmap={'rfilter':[]}
    for field in snapconf.JSON_FIELDS:
        legacy_fieldname = field
        if field in legacy_remap:
            legacy_fieldname = legacy_remap[field]
        if field in clause or legacy_fieldname in clause:
            submitted_fname = field
            if legacy_fieldname in clause:
                submitted_fname = legacy_fieldname
            if field not in fields:
                fields[field]=[]
            #adds array of values to a new entry in this field's array
            fields[field].append(clause[submitted_fname])
            #hack to support legacy query format (temporary), we're only assuming one val per array
            if field not in snapconf.RANGE_FIELDS:
                #adjust to map intervals and genes to same array
                if field == 'genes':
                    field = 'intervals'
                if field not in fmap:
                    fmap[field]=[]
                #allow more than one snaptron id, but convert to a ',' separated list
                if field == 'ids':
                    fmap[field].extend(clause[submitted_fname])
                elif field == 'sample_fields':
                    fmap[field].append(clause[submitted_fname])
                #otherwise only grab the first one (no nested OR)
                else:
                    fmap[field].append(clause.get(submitted_fname)[0])
            else:
                #for now we just return one range filter (no nested OR)
                rmap = clause.get(submitted_fname)[0]
                fmap['rfilter'].append("%s%s%s" % (field,rmap['op'],rmap['val']))
    #for now we just return one interval/gene (no nested OR)
    intervalqs=[]
    if 'intervals' in fmap:
        intervalqs = [fmap['intervals'][0]]
    #for now we just return one keyword (no nested OR)
    sampleqs = []
    if 'metadata_keywords' in fmap:
        sampleqs = fmap['metadata_keywords'][0]
    idqs = []
    if 'ids' in fmap:
        idqs=fmap['ids']
    if 'sample_fields' in fmap:
        fields = fmap['sample_fields']
        ra=ra._replace(sample_fields=fields[0].split(','))
    rangeqs = {'rfilter':fmap['rfilter']}
    return (intervalqs,rangeqs,sampleqs,idqs,ra)

def process_params(input_,region_args=default_region_args):
    params = {'regions':[],'ids':[],'rfilter':[],'sfilter':[],'fields':[],'result_count':False,'contains':'0','within':'0','exact':'0','return_format':snapconf.TSV,'score_by':'samples_count','coordinate_string':'','header':'1'}
    params_ = input_.split('&')
    for param_ in params_:
        (key,val) = param_.split("=")
        if key not in params:
            sys.stderr.write("unknown parameter %s, exiting\n" % key)
            sys.exit(-1)
        if key == 'regions' or key == 'ids':
            subparams = val.split(',')
            for subparam in subparams:
                params[key].append(subparam)
        elif key == 'fields':
            fields = val.split(',')
            for field in fields:
                if field == 'rc':
                    #only provide the total count of results
                    params['result_count'] = True
                    continue
                REQ_FIELDS.append(snapconf.INTRON_HEADER_FIELDS_MAP[field])
        elif key == 'rfilter':
            #url decode the rfilters:
            val = urllib.unquote(val)
            params[key].append(val) 
        else:
            if isinstance(params[key], list):
                params[key].append(val) 
            else:
                params[key]=val
    ra=region_args._replace(post=False,result_count=params['result_count'],contains=bool(int(params['contains'])),within=(int(params['within'])),exact=bool(int(params['exact'])),score_by=params['score_by'],print_header=bool(int(params['header'])),return_format=params['return_format'],original_input_string=input_,coordinate_string=params['coordinate_string'])
    return (params['regions'],params['ids'],{'rfilter':params['rfilter']},params['sfilter'],ra)

def process_post_params(input_,region_args=default_region_args):
    '''takes the more extensible JSON from a POST and converts it into a basic query assuming only 1 value per distinct argument'''
    jstring = list(input_)
    jstring = ''.join(jstring)
    js = json.loads(jstring)
    #for now assume only one OR clause (so no ORing)
    #clause = js[0]
    ra=region_args._replace(post=True,original_input_string=input_)
    or_intervals = []
    or_ranges = []
    or_samples = []
    or_ids = []
    for clause in js:
        (intervals,ranges,samples,ids,ra) = parse_json_query(clause,region_args=ra)
        or_intervals.append(intervals)
        or_ranges.append(ranges)
        or_samples.append(samples)
        or_ids.append(ids)
    return (or_intervals,or_ranges,or_samples,or_ids,ra)


def load_cpickle_file(filepath, compressed=False):
    ds = None
    if os.path.exists(filepath):
        if compressed:
            with gzip.GzipFile(filepath,"rb") as f:
                ds=cPickle.load(f)
        else: 
            with open(filepath,"rb") as f:
                ds=cPickle.load(f)
    return ds

def store_cpickle_file(filepath, ds, compress=False):
    if not os.path.exists(filepath):
        if compress:
            with gzip.GzipFile(filepath,"wb") as f:
                cPickle.dump(ds,f,cPickle.HIGHEST_PROTOCOL)
        else:
            with open(filepath,"wb") as f:
                cPickle.dump(ds,f,cPickle.HIGHEST_PROTOCOL)
        return True
    return False

def retrieve_from_db_by_ids(dbh,select,ids):
    wheres = ['?' for x in ids]
    select = "%s (%s);" % (select,','.join(wheres))
    ids_ = [int(id_) for id_ in ids]
    return dbh.execute(select,ids_)

class GeneCoords(object):

    def __init__(self,load_refseq=True,load_canonical=True,load_transcript=False):
        self.ensembl_id_patt = re.compile('(ENST\d+)')
        if load_refseq:
            gene_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.REFSEQ_ANNOTATION)
            gene_pickle_file = "%s.pkl" % (gene_file)
            self.gene_map = load_cpickle_file(gene_pickle_file)
            if not self.gene_map:
                self.load_gene_coords(gene_file)
            store_cpickle_file(gene_pickle_file,self.gene_map)
        if load_canonical:
            canonical_gene_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.CANONICAL_ANNOTATION)
            canonical_gene_pickle_file = "%s.pkl" % (canonical_gene_file)
            self.canonical_gene_map = load_cpickle_file(canonical_gene_pickle_file)
            if not self.canonical_gene_map:
                self.load_canonical_gene_coords(canonical_gene_file)
            store_cpickle_file(canonical_gene_pickle_file,self.canonical_gene_map)
       
        #per transcript exons
        if load_transcript:
            transcript_file = "%s/%s" % (snapconf.TABIX_DB_PATH,snapconf.TABIX_GENE_INTERVAL_DB)
            transcript_pickle_file = "%s.pkl" % (transcript_file)
            self.transcript_map = load_cpickle_file(transcript_pickle_file)
            if not self.transcript_map:
                self.load_transcripts(transcript_file)
            store_cpickle_file(transcript_pickle_file,self.transcript_map)

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
            sys.stderr.write("ERROR no gene found by name %s\n" % (geneq))
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

