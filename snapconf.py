#!/usr/bin/env python2.7
import operator
import re

import lucene
from org.apache.lucene.index import IndexReader
from org.apache.lucene.index import Term
from org.apache.lucene.search import NumericRangeQuery
from org.apache.lucene.document import Document, Field, IntField, FloatField, StringField, TextField, StoredField

TERM = Term
NIR = NumericRangeQuery.newIntRange
NFR = NumericRangeQuery.newFloatRange

#from collections import namedtuple
#bunch of constants for use throughout snaptron

operators={'>=':operator.ge,'<=':operator.le,'>':operator.gt,'<':operator.lt,'=':operator.eq,'!=':operator.ne}
TABIX="tabix"
#TABIX_INTERVAL_DB='all_SRA_introns_ids_stats.tsv.gz'
TABIX_INTERVAL_DB='all_SRA_introns_ids_stats.tsv.new2_w_sourcedb2.gz'
TABIX_DB_PATH='/data2/gigatron2'
TABIX_DBS={'chromosome':TABIX_INTERVAL_DB,'length':'by_length.gz','snaptron_id':'by_id.gz','samples_count':'by_sample_count.gz','coverage_sum':'by_coverage_sum.gz','coverage_avg':'by_coverage_avg.gz','coverage_median':'by_coverage_median.gz'}
SAMPLE_MD_FILE='/data2/gigatron2/all_illumina_sra_for_human_ids.tsv'
SAMPLE_IDS_COL=12
SAMPLE_ID_COL=0
INTRON_ID_COL=0

#search by gene constants
REFSEQ_ANNOTATION='refFlat.hg19.txt.sorted'
INTERVAL_PATTERN = re.compile(r'^chr[12]?[0-9XYM]:\d+-\d+$')
CHROM_PATTERN = re.compile(r'^chr[12]?[0-9XYM]$')
MAX_GENE_PROXIMITY = 10000

#set much larger than the total # of introns we expect to have
LUCENE_MAX_RANGE_HITS=100000000
#set much larger than the total # of samples we expect to have
LUCENE_MAX_SAMPLE_HITS=1000000

LUCENE_TYPES={'snaptron_id':[IntField,int,NIR],'length':[IntField,int,NIR],'strand':[StringField,str,TERM],'annotated?':[IntField,int,NIR],'left_motif':[StringField,str,TERM],'right_motif':[StringField,str,TERM],'left_annotated?':[TextField,str,TERM],'right_annotated?':[TextField,str,TERM],'length':[IntField,int,NIR],'samples_count':[IntField,int,NIR],'coverage_sum':[IntField,int,NIR],'coverage_avg':[FloatField,float,NFR],'coverage_median':[FloatField,float,NFR],'source_dataset_id':[IntField,int,NIR],'coverage_avg2':[FloatField,float,NFR],'coverage_median2':[FloatField,float,NFR]}

RANGE_QUERY_DELIMITER=','
RANGE_QUERY_OPS='([=><!]+)'
RANGE_QUERY_FIELD_PATTERN=re.compile(RANGE_QUERY_OPS)
SAMPLE_QUERY_DELIMITER='==='
SAMPLE_QUERY_FIELD_DELIMITER='::'

FLOAT_FIELDS=set(['coverage_avg','coverage_median'])

DATA_SOURCE='SRA'
#may have to adjust this parameter for performance (# of tabix calls varies inversely with this number)
MAX_DISTANCE_BETWEEN_IDS=1000
#INTRON_URL='http://localhost:8090/solr/gigatron/select?q='
#SAMPLE_URL='http://localhost:8090/solr/sra_samples/select?q='

#setup headers for both the original intron list and the sample metadata list
INTRON_HEADER='snaptron_id	chromosome	start	end	length	strand	annotated?	left_motif	right_motif	left_annotated?	right_annotated?	samples	read_coverage_by_sample	samples_count	coverage_sum	coverage_avg	coverage_median	source_dataset_id'

SAMPLE_HEADER='intropolis_sample_id_i	run_accession_s	sample_accession_s	experiment_accession_s	study_accession_s	submission_accession_s	sra_ID_s	run_ID_s	run_alias_t	run_date_t	updated_date_t	spots_s	bases_s	run_center_t	experiment_name_t	run_attribute_t	experiment_ID_s	experiment_alias_t	experiment_title_t	study_name_t	sample_name_t	design_description_t	library_name_t	library_strategy_s	library_source_t	library_selection_t	library_layout_t	library_construction_protocol_t	read_spec_t	platform_t	instrument_model_t	platform_parameters_t	experiment_url_link_s	experiment_attribute_t	sample_ID_s	sample_alias_t	taxon_id_s	common_name_t	description_t	sample_url_link_s	sample_attribute_t	study_ID_s	study_alias_t	study_title_t	study_type_t	study_abstract_t	center_project_name_t	study_description_t	study_url_link_s	study_attribute_t	related_studies_t	primary_study_s	submission_ID_s	submission_comment_t	submission_center_t	submission_lab_t	submission_date_t	sradb_updated.x_s	fastq_ID_s	file_name_t	md5_s	bytes_s	audit_time_s	sradb_updated_file_s	date_download_t	URL_s	layout_s	URL_R_s	md5_R_s	cell_type_t	tissue_t	cell_line_t	strain_t	age_s	disease_t	population_t	sex_s	source_name_s'

INTRON_HEADER_FIELDS=INTRON_HEADER.split('\t')
INTRON_HEADER_FIELDS_MAP={}
for (i,field) in enumerate(INTRON_HEADER_FIELDS):
   INTRON_HEADER_FIELDS_MAP[field]=i 

SAMPLE_HEADER_FIELDS=SAMPLE_HEADER.split('\t')
SAMPLE_HEADER_FIELDS_MAP={}
for (i,field) in enumerate(SAMPLE_HEADER_FIELDS):
   SAMPLE_HEADER_FIELDS_MAP[field]=i 
