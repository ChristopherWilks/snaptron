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

#to force the overlap to have either the start within the interval or the end
#useful for avoiding overlaps which only contain the query interval
EITHER_START=1
EITHER_END=2

BULK_QUERY_DELIMITER='\|\|\|'

#return formats:
TSV='0'
UCSC_BED='1'
UCSC_URL='2'


RegionArgs = namedtuple('RegionArgs','tabix_db_file range_filters intron_filter sample_filter save_introns save_samples stream_back print_header header prefix cut_start_col region_start_col region_end_col contains either exact result_count return_format score_by post original_input_string coordinate_string sample_fields sid_search_object sids additional_cmd debug')

default_region_args = RegionArgs(tabix_db_file=snapconf.TABIX_INTERVAL_DB, range_filters=[], intron_filter=None, sample_filter=None, save_introns=False, save_samples=False, stream_back=True, print_header=True, header="DataSource:Type\t%s" % snapconf.INTRON_HEADER, prefix="%s:I" % snapconf.DATA_SOURCE, cut_start_col=snapconf.CUT_START_COL, region_start_col=snapconf.INTERVAL_START_COL, region_end_col=snapconf.INTERVAL_END_COL, contains=False, either=0, exact=False, result_count=False, return_format=TSV, score_by="samples_count", post=False, original_input_string='', coordinate_string='', sample_fields=[], sid_search_object=None, sids=[], additional_cmd='', debug=True)
