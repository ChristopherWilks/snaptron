#!/usr/bin/env python2.7
#SERVICE_URL='http://stingray.cs.jhu.edu:8090/srav2'
SERVICE_URL='http://stingray.cs.jhu.edu:8090/srav1'
BUFFER_SIZE_BYTES=1024*1024
CACHE_SAMPLE_METADTA=True
#TODO use python tmp
TMPDIR='/tmp'
FIELD_ARGS={'region':['"chr#:start-end"',str,None,'either a simple genomic region (e.g. chr1:1-1000) or a gene fusion pair (e.g. EML4-ALK)'],
      'thresholds':['"coverage_sum>=5&annotated=1"',str,None,'one or more junction specific thresholds/filters'], 
      'filters':['"design_description: cortex"',str,None,'one or more sample specific filters passed to Lucene (using the Lucene query langage)'],
      'contains':['1',str,None,'search for only junctions which have both their genomic coordinates within (inclusive) the specified region'],
      'exact':['1',str,None,'search for only junctions which have both their genomic coordinates matching exactly the specified region\'s start/end coordinates'],
      'within':['2',str,None,'search for only junctions which have one or the other of their genomic coordinates within (inclusive) of the specified region, 1=left coordinte;2=right coordinate']}
SAMPLE_IDS_COL=12
INTRON_ID_COL=1
INTERVAL_CHR_COL=2
INTERVAL_START_COL=3
INTERVAL_END_COL=4
MIN_EXON_SIZE = 1

