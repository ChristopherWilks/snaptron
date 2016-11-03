#!/usr/bin/env python2.7
import operator
import re

import lucene
from org.apache.lucene.index import IndexReader
from org.apache.lucene.index import Term
from org.apache.lucene.search import NumericRangeQuery
from org.apache.lucene.document import Document, Field, IntField, FloatField, StringField, TextField, StoredField

#####fields that need to be changed for a different instance
DATA_SOURCE='SRAv2'
IP='127.0.0.1'
PORT=1556
SERVER_STRING='http://stingray.cs.jhu.edu:8090/srav2/'
HG='hg38'
BIGWIG2WIG="bigWigToWig"
ROOT_DIR='./'
PYTHON_PATH="python"
TABIX="tabix"
#tabix related
TABIX_DB_PATH='./data'
TABIX_GENE_INTERVAL_DB='gensemrefg.hg38_annotations.gtf.sorted.gz'
TABIX_INTERVAL_DB='intropolis.v2.hg38.tsv.snaptron2.bgzip'
TABIX_IDS_DB='by_idV2.gz'
ID_START_COL=2
CUT_START_COL=1
#sqlite3 dbs
SAMPLE_SQLITE_DB="%s/by_sample_ids.v2.sqlite3" % (TABIX_DB_PATH)
SNAPTRON_SQLITE_DB="%s/snaptronV2.sqlite3" % (TABIX_DB_PATH)
#Lucene dbs
LUCENE_SAMPLE_DB="%s/lucene_v2/" % (TABIX_DB_PATH)
LUCENE_RANGE_DB="%s/lucene_ranges_v1/" % (TABIX_DB_PATH)
#gene annotation related flat files
REFSEQ_ANNOTATION='refFlat.hg38.txt.sorted'
CANONICAL_ANNOTATION='hg38.ucsc_known_canonical.tsv'
SAMPLE_MD_FILE="%s/illumina_sra_for_human_ids.v2.tsv" % (TABIX_DB_PATH)
COSMIC_FUSION_FILE="%s/CosmicFusionExport.tsv.gz" % (TABIX_DB_PATH)
#####END of fields that need to be changed for a different instance


#basic paths to everything (one day replace with inferred directory)
#used only by snaptron_server
#mostly used by snaptronws.py
SNAPTRON_APP = "%s/snaptron.py" % (ROOT_DIR)
SAMPLES_APP = "%s/snample.py" % (ROOT_DIR)
ANNOTATIONS_APP = "%s/snannotation.py" % (ROOT_DIR)
DENSITY_APP = "%s/sdensity.py" % (ROOT_DIR)
BREAKPOINT_APP = "%s/sbreakpoint.py" % (ROOT_DIR)
#size for the OS buffer on the input pipe reading from samtools output
CMD_BUFFER_SIZE = -1
#a low max for what we want to pass to samtools for start/end coordinates, otherwise samtools will return everything
MAX_COORDINATE_DIGITS = 11
#size of samtools read,can impact performance in a major way
READ_SIZE = 16777216
#for test read much smaller chunks
#READ_SIZE=32
RANGE_PATTERN = re.compile(r'^[0-9a-zA-Z_\-]+:\d+-\d+$')
#cant have anything else in the data path or its probably a security issue
READ_SIZE_PATTERN = re.compile(r'^\d+$')

TERM = Term
NIR = NumericRangeQuery.newIntRange
NFR = NumericRangeQuery.newFloatRange

operators_old={'>=':operator.ge,'<=':operator.le,'>':operator.gt,'<':operator.lt,'=':operator.eq,'!=':operator.ne}
operators={'>:':operator.ge,'<:':operator.le,'>':operator.gt,'<':operator.lt,':':operator.eq,'!:':operator.ne}
#we overloaded this map to be used for all searchable fields, not just those with TABIX dbs
TABIX_DBS={'chromosome':TABIX_INTERVAL_DB,'intervals':TABIX_INTERVAL_DB,'genes':'','length':'by_length.gz','snaptron_id':TABIX_IDS_DB,'samples_count':'by_sample_count.gz','coverage_sum':'by_coverage_sum.gz','coverage_avg':'by_coverage_avg.gz','coverage_median':'by_coverage_median.gz','metadata_keyword':'','sample_id':'by_sample_id.gz','ids':'','annotated':'','left_annotated':'','right_annotated':''}
RANGE_FIELDS = ['length','samples_count','coverage_sum','coverage_avg','coverage_median']
JSON_FIELDS=set(['intervals','genes','ids','metadata_keywords','sample_fields'])
JSON_FIELDS.update(RANGE_FIELDS)
SAMPLE_IDS_COL=12
SAMPLE_ID_COL=0
SAMPLES_COUNT_COL=13
INTRON_ID_COL=0
INTERVAL_START_COL=2
INTERVAL_END_COL=3
GENE_START_COL=3
GENE_END_COL=4
STRAND_COL=5


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

LUCENE_TYPES={'snaptron_id':[IntField,int,NIR],'length':[IntField,int,NIR],'strand':[StringField,str,TERM],'annotated':[IntField,int,NIR],'left_motif':[StringField,str,TERM],'right_motif':[StringField,str,TERM],'left_annotated':[TextField,str,TERM],'right_annotated':[TextField,str,TERM],'length':[IntField,int,NIR],'samples_count':[IntField,int,NIR],'coverage_sum':[IntField,int,NIR],'coverage_avg':[FloatField,float,NFR],'coverage_median':[FloatField,float,NFR],'source_dataset_id':[IntField,int,NIR],'coverage_avg2':[FloatField,float,NFR],'coverage_median2':[FloatField,float,NFR]}


RANGE_QUERY_DELIMITER=','
RANGE_QUERY_OPS='([:><!]+)'
RANGE_QUERY_FIELD_PATTERN=re.compile(RANGE_QUERY_OPS)
SAMPLE_QUERY_DELIMITER='==='
SAMPLE_QUERY_FIELD_DELIMITER=':' #::

FLOAT_FIELDS=set(['coverage_avg','coverage_median'])

#may have to adjust this parameter for performance (# of tabix calls varies inversely with this number)
MAX_DISTANCE_BETWEEN_IDS=1000
#INTRON_URL='http://localhost:8090/solr/gigatron/select?q='
#SAMPLE_URL='http://localhost:8090/solr/sra_samples/select?q='

#GENE_ANNOTATION_HEADER (GTF)
GENE_ANNOTATION_HEADER = "DataSource:Type\treference\tannotation_source\tfeature_type\tstart\tend\tscore\tstrand\tunused\tattributes";

#setup headers for both the original intron list and the sample metadata list
INTRON_HEADER='snaptron_id	chromosome	start	end	length	strand	annotated	left_motif	right_motif	left_annotated	right_annotated	samples	read_coverage_by_sample	samples_count	coverage_sum	coverage_avg	coverage_median	source_dataset_id'
INTRON_TYPE_HEADER_MAP={'snaptron_id':int,'chromosome':str,'start':int,'end':int,'length':int,'strand':str,'annotated':bool,'left_motif':str,'right_motif':str,'left_annotated':str,'right_annotated':str,'samples':str,'read_coverage_by_sample':str,'samples_count':int,'coverage_sum':int,'coverage_avg':float,'coverage_median':float,'source_dataset_id':str}

SAMPLE_HEADER='intropolis_sample_id_i	run_accession_s	sample_accession_s	experiment_accession_s	study_accession_s	submission_accession_s	sra_ID_s	run_ID_s	run_alias_t	run_date_t	updated_date_t	spots_s	bases_s	run_center_t	experiment_name_t	run_attribute_t	experiment_ID_s	experiment_alias_t	experiment_title_t	study_name_t	sample_name_t	design_description_t	library_name_t	library_strategy_s	library_source_t	library_selection_t	library_layout_t	library_construction_protocol_t	read_spec_t	platform_t	instrument_model_t	platform_parameters_t	experiment_url_link_s	experiment_attribute_t	sample_ID_s	sample_alias_t	taxon_id_s	common_name_t	description_t	sample_url_link_s	sample_attribute_t	study_ID_s	study_alias_t	study_title_t	study_type_t	study_abstract_t	center_project_name_t	study_description_t	study_url_link_s	study_attribute_t	related_studies_t	primary_study_s	submission_ID_s	submission_comment_t	submission_center_t	submission_lab_t	submission_date_t	sradb_updated.x_s	fastq_ID_s	file_name_t	md5_s	bytes_s	audit_time_s	sradb_updated_file_s	date_download_t	URL_s	layout_s	URL_R_s	md5_R_s	cell_type_t	tissue_t	cell_line_t	strain_t	age_s	disease_t	population_t	sex_s	source_name_s'

INTRON_HEADER_FIELDS=INTRON_HEADER.split('\t')
INTRON_HEADER_FIELDS_MAP={}
INTRON_TYPE_HEADER_=[]
for (i,field) in enumerate(INTRON_HEADER_FIELDS):
   INTRON_HEADER_FIELDS_MAP[field]=i
   INTRON_TYPE_HEADER_.append(INTRON_TYPE_HEADER_MAP[field].__name__)
INTRON_TYPE_HEADER = "\t".join(INTRON_TYPE_HEADER_)

SAMPLE_HEADER_FIELDS=SAMPLE_HEADER.split('\t')
SAMPLE_HEADER_FIELDS_MAP={}
SAMPLE_HEADER_FIELDS_TYPE_MAP={}
for (i,field) in enumerate(SAMPLE_HEADER_FIELDS):
   SAMPLE_HEADER_FIELDS_MAP[field]=i
   fields = field.split('_')
   t = fields[-1]
   field_wo_type = '_'.join(fields[:-1])
   SAMPLE_HEADER_FIELDS_TYPE_MAP[field_wo_type]=field
