#!/usr/bin/env Python2.7

#based on the example code at
#http://graus.nu/blog/pylucene-4-0-in-60-seconds-tutorial/

import sys
import re
import os
import lucene
 
from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.document import Document, Field, LongField, StringField, TextField, FloatField
from org.apache.lucene.search import NumericRangeQuery
from org.apache.lucene.document import FieldType
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version


LUCENE_TYPES={'i':LongField,'s':StringField,'t':TextField,'f':FloatField,'NA':TextField}
LUCENE_TYPE_METHODS={'i':NumericRangeQuery.newLongRange,'f':NumericRangeQuery.newFloatRange}
PREC_STEP=1
LUCENE_TYPES_FILE='./lucene_indexed_numeric_types.tsv'

float_patt = re.compile(r'\tf,')
def process_pre_inferred_types(types_map,typesF):
    with open(typesF,"r") as fin:
        for line in fin:
            fields = line.rstrip().split('\t')
            #expected pre-sorted fields based on maximum occurrence
            #assume if strings are present but not plurality, we'll put null in
            typechar = fields[1][0]
            if typechar != 'f' and float_patt.search(line):
                types_map.append(["",LUCENE_TYPES['f'],typechar])
            else:
                types_map.append(["",LUCENE_TYPES[typechar],typechar])
                  
 
if __name__ == "__main__":
  types_map = []
  if len(sys.argv) <= 1:
      sys.stderr.write("must pass in the inferred types file, exiting\n")

  typesF = sys.argv[1]
  process_pre_inferred_types(types_map,typesF) 

  output_path = "."
  if len(sys.argv) > 2:
      output_path = sys.argv[2]


  lucene.initVM()
  analyzer = StandardAnalyzer(Version.LUCENE_4_10_1)
  analyzer_ws = WhitespaceAnalyzer(Version.LUCENE_4_10_1)
  std_path = "%s/lucene_full_standard/" % (output_path)
  ws_path = "%s/lucene_full_ws/" % (output_path)
  if os.path.exists(std_path):
      os.remove(std_path)
  if os.path.exists(ws_path):
      os.remove(ws_path)
  indexDir1 = SimpleFSDirectory(File(std_path))
  indexDir2 = SimpleFSDirectory(File(ws_path))
  writerConfig1 = IndexWriterConfig(Version.LUCENE_4_10_1, analyzer)
  writerConfig2 = IndexWriterConfig(Version.LUCENE_4_10_1, analyzer_ws)
  writer1 = IndexWriter(indexDir1, writerConfig1)
  writer2 = IndexWriter(indexDir2, writerConfig2)
 
  print "%d docs in index1" % writer1.numDocs()
  print "%d docs in index2" % writer2.numDocs()
  print "Reading lines from sys.stdin..."
    
  ftypes = open(LUCENE_TYPES_FILE, "w")
  
  for n, l in enumerate(sys.stdin):
    doc = Document()
    fields = l.rstrip().split("\t")
    all_ = []
    if n == 0:
        sys.stdout.write("TYPES_HEADER")
    elif n == 1:
        sys.stdout.write("\n")
    for (idx,field) in enumerate(fields):
        if n == 0:
            types_map[idx][0] = field
            fieldtypechar = types_map[idx][2]
            ftypes.write("%s\t%s\n" % (field, fieldtypechar))
            sys.stdout.write("\t"+field+"_"+types_map[idx][2])
        if n >= 1:
            all_.append(field)
            (fname,fieldtype,fieldtypechar) = types_map[idx]
            sys.stdout.write("%s %s %s %d %d\n" % (fname,fieldtype,field,idx,n))
            #basically this is complex to handle NA's in numeric fields
            field_object = None
            ft = FieldType()
            ft.setStored(True)
            ft.setIndexed(True)
            ft.setNumericPrecisionStep(PREC_STEP)
            try:
                if fieldtype is FloatField:
                    field = float(field)
                    ft.setNumericType(FieldType.NumericType.FLOAT)
                    field_object = fieldtype(fname, field, ft)
                elif fieldtype is LongField:
                    field = long(field) 
                    ft.setNumericType(FieldType.NumericType.LONG)
                    field_object = fieldtype(fname, field, ft)
                else:
                    field_object = fieldtype(fname, field, Field.Store.YES)
            except ValueError, e:
                field = None
            if field is not None:
                doc.add(field_object)
    if n > 0:
        all_fields = ' '.join(all_)
        doc.add(TextField('all', all_fields, Field.Store.NO))
    writer1.addDocument(doc)
    writer2.addDocument(doc)
  print "Indexed %d lines from stdin (%d docs in index)" % (n, writer1.numDocs())
  print "Closing index of %d docs..." % writer1.numDocs()
  print "Indexed %d lines from stdin (%d docs in index)" % (n, writer2.numDocs())
  print "Closing index of %d docs..." % writer2.numDocs()
  writer1.close()
  writer2.close()
  ftypes.close()

