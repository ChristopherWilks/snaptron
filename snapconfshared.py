#!/usr/bin/env python

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

from collections import namedtuple
import re
import operator
import logging
from logging import handlers

import snapconf

logger = logging.getLogger("snaptron.%s" % (snapconf.DATA_SOURCE))
logger.setLevel(logging.INFO)


import lucene
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.document import Field, LegacyLongField, LegacyFloatField, StringField, TextField
from org.apache.lucene.index import Term
from org.apache.lucene.search import LegacyNumericRangeQuery
from org.apache.lucene.util import Version
#setup lucene reader for sample related searches
lucene.initVM()
#use this for GTEx sample metadata
analyzer = StandardAnalyzer()
#use this for SRAvX sample metadata
analyzer_ws = WhitespaceAnalyzer()

#to force the overlap to have either the start within the interval or the end
#useful for avoiding overlaps which only contain the query interval
EITHER_START=1
EITHER_END=2

#different columns for base-level results
BASE_START_COL=1
BASE_END_COL=2

BULK_QUERY_DELIMITER='\|\|\|'

#path to compiled C binary to do speedy basic calculations on base coverage data
CALC_PATH='./scripts/groupby/calc'

#return formats:
TSV='0'
UCSC_BED='1'
UCSC_URL='2'
UCSC_WIG='3'
UCSC_URL_WIG='4'

GENCODE_ANNOTATION='gencode.v25.annotation.gff3.gz'
GENE_ID_PATTERN=re.compile(r'ENSG\d+\.\d+')

SAMPLE_GROUP_IDS_COL=3

#setup headers for both the original intron list and the sample metadata list
INTRON_HEADER='snaptron_id	chromosome	start	end	length	strand	annotated	left_motif	right_motif	left_annotated	right_annotated	samples	samples_count	coverage_sum	coverage_avg	coverage_median	source_dataset_id'
INTRON_TYPE_HEADER_MAP={'snaptron_id':int,'chromosome':str,'start':int,'end':int,'length':int,'strand':str,'annotated':bool,'left_motif':str,'right_motif':str,'left_annotated':str,'right_annotated':str,'samples':str,'samples_count':int,'coverage_sum':int,'coverage_avg':float,'coverage_median':float,'source_dataset_id':str}

INTRON_HEADER_FIELDS=INTRON_HEADER.split('\t')
INTRON_HEADER_FIELDS_MAP={}
INTRON_TYPE_HEADER_=[]
for (i,field) in enumerate(INTRON_HEADER_FIELDS):
   INTRON_HEADER_FIELDS_MAP[field]=i
   INTRON_TYPE_HEADER_.append(INTRON_TYPE_HEADER_MAP[field].__name__)
INTRON_TYPE_HEADER = "\t".join(INTRON_TYPE_HEADER_)

GENE_HEADER='snaptron_id	chromosome	start	end	length	strand	NA	NA	NA	exon_count	gene_id:gene_name:gene_type:bp_length	samples	samples_count	coverage_sum	coverage_avg	coverage_median	compilation_id'
EXON_HEADER=''
annotated_columns=set(['annotated','left_annotated','right_annotated'])




#for injection checking
calc_axis_ops = set(["0","1","sum","mean"])
label_pattern = re.compile(r'^[a-zA-Z0-9_\-:;\.]+$')

#params that set paths and binaries
ROOT_DIR='./'
PYTHON_PATH="python"
BIGWIG2WIG="bigWigToWig"

#tabix related
TABIX="tabix"
TABIX_DB_PATH='./data'
TABIX_GENE_INTERVAL_DB='all_transcripts.gtf.bgz'
TABIX_INTERVAL_DB='junctions_uncompressed.bgz'
GENE_TABIX_DB='genes.bgz'
EXON_TABIX_DB='exons.bgz'
BASE_TABIX_DB='bases.bgz'
#split by chromosome for space and performance reasons
BASE_TABIX_DB_PATH='%s/bases/' % TABIX_DB_PATH

#sqlite3 dbs
SQLITE="sqlite3"
SAMPLE_SQLITE_DB="%s/sample2junction.sqlite" % (TABIX_DB_PATH)
SNAPTRON_SQLITE_DB="%s/junctions.sqlite" % (TABIX_DB_PATH)
GENE_SQLITE_DB="%s/genes.sqlite" % (TABIX_DB_PATH)
EXON_SQLITE_DB="%s/exons.sqlite" % (TABIX_DB_PATH)

#gene annotation related flat files
GENE_INTERVAL_DB='%s/transcripts.sqlite' % (TABIX_DB_PATH)
REFSEQ_ANNOTATION='refseq_transcripts_by_hgvs.tsv'
CANONICAL_ANNOTATION='ucsc_known_canonical_transcript.tsv'

#sample metadata
SAMPLE_MD_FILE="%s/samples.tsv" % (TABIX_DB_PATH)
SAMPLE_GROUP_FILE="%s/%s" % (TABIX_DB_PATH,'samples.groups.tsv')
LUCENE_STD_ANALYZER=analyzer_ws
LUCENE_WS_ANALYZER=analyzer
#Lucene dbs
LUCENE_STD_SAMPLE_DB="%s/lucene_full_standard/" % (TABIX_DB_PATH)
LUCENE_WS_SAMPLE_DB="%s/lucene_full_ws/" % (TABIX_DB_PATH)

#basic paths to everything (one day replace with inferred directory)
#used only by snaptron_server
#mostly used by snaptronws.py
SNAPTRON_APP = "%s/snaptron.py" % (ROOT_DIR)
SAMPLES_APP = "%s/snample.py" % (ROOT_DIR)
ANNOTATIONS_APP = "%s/snannotation.py" % (ROOT_DIR)
GENES_APP='genes'
EXONS_APP='exons'
BASES_APP='bases'
pseudo_apps = set([GENES_APP,EXONS_APP,BASES_APP])
#size for the OS buffer on the input pipe reading from samtools output
CMD_BUFFER_SIZE = -1
#a low max for what we want to pass to samtools for start/end coordinates, otherwise samtools will return everything
MAX_COORDINATE_DIGITS = 11
#size of samtools read,can impact performance in a major way
#lowering it here helps queries which have smaller per-record sizes respond faster
#but too low, and larger queries will suffer, set to 1MiB
READ_SIZE = 1048576
#for test read much smaller chunks
#READ_SIZE=32
RANGE_PATTERN = re.compile(r'^[0-9a-zA-Z_\-]+:\d+-\d+$')
#cant have anything else in the data path or its probably a security issue
READ_SIZE_PATTERN = re.compile(r'^\d+$')

TERM = Term
NIR = LegacyNumericRangeQuery.newIntRange
NFR = LegacyNumericRangeQuery.newFloatRange

operators_old={'>=':operator.ge,'<=':operator.le,'>':operator.gt,'<':operator.lt,'=':operator.eq,'!=':operator.ne}
operators={'>:':operator.ge,'<:':operator.le,'>':operator.gt,'<':operator.lt,':':operator.eq,'!:':operator.ne}
#we overloaded this map to be used for all searchable fields, not just those with TABIX dbs
TABIX_DBS={'chromosome':TABIX_INTERVAL_DB,'intervals':TABIX_INTERVAL_DB,'genes':'','length':'by_length.gz','snaptron_id':None,'samples_count':'by_sample_count.gz','coverage_sum':'by_coverage_sum.gz','coverage_avg':'by_coverage_avg.gz','coverage_median':'by_coverage_median.gz','metadata_keyword':'','sample_id':'by_sample_id.gz','ids':'','annotated':'','left_annotated':'','right_annotated':'','strand':''}
RANGE_FIELDS = ['length','samples_count','coverage_sum','coverage_avg','coverage_median','strand']
JSON_FIELDS=set(['intervals','genes','ids','metadata_keywords','sample_fields'])
JSON_FIELDS.update(RANGE_FIELDS)
SAMPLE_IDS_COL=11
INTRON_ID_COL=0
CHROM_COL=1
INTERVAL_START_COL=2
INTERVAL_END_COL=3
GENE_START_COL=3
GENE_END_COL=4
STRAND_COL=5
DONOR_COL=7
ACCEPTOR_COL=8
COV_AVG_COL=14
COV_MED_COL=15


#search by gene constants
TABIX_PATTERN = re.compile(r'^([chrMXY\d]+):(\d+)-(\d+)$')
INTERVAL_PATTERN = re.compile(r'^(chr[12]?[0-9XYM]):(\d+)-(\d+)$')
CHROM_PATTERN = re.compile(r'^chr[12]?[0-9XYM]$')
SNAPTRON_ID_PATT = re.compile(r'snaptron_id')
MAX_GENE_PROXIMITY = 10000

#set much larger than the total # of introns we expect to have
LUCENE_MAX_RANGE_HITS=100000000
#set much larger than the total # of samples we expect to have
LUCENE_MAX_SAMPLE_HITS=1000000

LUCENE_TYPES={'snaptron_id':[LegacyLongField,long,NIR],'strand':[StringField,str,TERM],'annotated':[LegacyLongField,long,NIR],'left_motif':[StringField,str,TERM],'right_motif':[StringField,str,TERM],'left_annotated':[TextField,str,TERM],'right_annotated':[TextField,str,TERM],'length':[LegacyLongField,long,NIR],'samples_count':[LegacyLongField,long,NIR],'coverage_sum':[LegacyLongField,long,NIR],'coverage_avg':[LegacyFloatField,float,NFR],'coverage_median':[LegacyFloatField,float,NFR],'source_dataset_id':[LegacyLongField,long,NIR],'coverage_avg2':[LegacyFloatField,float,NFR],'coverage_median2':[LegacyFloatField,float,NFR]}


RANGE_QUERY_DELIMITER=','
RANGE_QUERY_OPS='([:><!]+)'
RANGE_QUERY_FIELD_PATTERN=re.compile(RANGE_QUERY_OPS)
SAMPLE_QUERY_DELIMITER='==='
SAMPLE_QUERY_FIELD_DELIMITER=':' #::

FLOAT_FIELDS=set(['coverage_avg','coverage_median'])

#may have to adjust this parameter for performance (# of tabix calls varies inversely with this number)
MAX_DISTANCE_BETWEEN_IDS=1000

DATA_SOURCE_HEADER='DataSource:Type'
#GENE_ANNOTATION_HEADER (GTF)
GENE_ANNOTATION_HEADER = DATA_SOURCE_HEADER + "\treference\tannotation_source\tfeature_type\tstart\tend\tscore\tstrand\tunused\tattributes";

RegionArgs = namedtuple('RegionArgs','tabix_db_file range_filters intron_filter sample_filter save_introns save_samples stream_back print_header header prefix cut_start_col id_col region_start_col region_end_col contains either exact result_count return_format score_by post original_input_string coordinate_string sample_fields sid_search_object sids additional_cmd sqlite_db_file fields_map fields_list app label calc calc_axis calc_op logger debug')

default_region_args = RegionArgs(tabix_db_file=TABIX_INTERVAL_DB, range_filters=[], intron_filter=None, sample_filter=None, save_introns=False, save_samples=False, stream_back=True, print_header=True, header="%s\t%s" % (DATA_SOURCE_HEADER,INTRON_HEADER), prefix="%s:I" % snapconf.DATA_SOURCE, cut_start_col=snapconf.CUT_START_COL, id_col = INTRON_ID_COL, region_start_col=INTERVAL_START_COL, region_end_col=INTERVAL_END_COL, contains=False, either=0, exact=False, result_count=False, return_format=TSV, score_by="samples_count", post=False, original_input_string='', coordinate_string='', sample_fields=[], sid_search_object=None, sids=[], additional_cmd='', sqlite_db_file=SNAPTRON_SQLITE_DB, fields_map=INTRON_HEADER_FIELDS_MAP, fields_list=INTRON_HEADER_FIELDS, app=SNAPTRON_APP, label="", calc=0, calc_axis="1", calc_op="sum", logger = logger, debug=False)
