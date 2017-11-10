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
import snapconf
import re

#to force the overlap to have either the start within the interval or the end
#useful for avoiding overlaps which only contain the query interval
EITHER_START=1
EITHER_END=2

#different columns for base-level results
BASE_START_COL=1
BASE_END_COL=2

BULK_QUERY_DELIMITER='\|\|\|'

#return formats:
TSV='0'
UCSC_BED='1'
UCSC_URL='2'

GENCODE_ANNOTATION='gencode.v25.annotation.gff3.gz'
GENE_ID_PATTERN=re.compile(r'ENSG\d+\.\d+')

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

RegionArgs = namedtuple('RegionArgs','tabix_db_file range_filters intron_filter sample_filter save_introns save_samples stream_back print_header header prefix cut_start_col id_col region_start_col region_end_col contains either exact result_count return_format score_by post original_input_string coordinate_string sample_fields sid_search_object sids additional_cmd sqlite_db_file fields_map fields_list debug')

default_region_args = RegionArgs(tabix_db_file=snapconf.TABIX_INTERVAL_DB, range_filters=[], intron_filter=None, sample_filter=None, save_introns=False, save_samples=False, stream_back=True, print_header=True, header="%s\t%s" % (snapconf.DATA_SOURCE_HEADER,INTRON_HEADER), prefix="%s:I" % snapconf.DATA_SOURCE, cut_start_col=snapconf.CUT_START_COL, id_col = snapconf.INTRON_ID_COL, region_start_col=snapconf.INTERVAL_START_COL, region_end_col=snapconf.INTERVAL_END_COL, contains=False, either=0, exact=False, result_count=False, return_format=TSV, score_by="samples_count", post=False, original_input_string='', coordinate_string='', sample_fields=[], sid_search_object=None, sids=[], additional_cmd='', sqlite_db_file=snapconf.SNAPTRON_SQLITE_DB, fields_map=INTRON_HEADER_FIELDS_MAP, fields_list=INTRON_HEADER_FIELDS, debug=True)
