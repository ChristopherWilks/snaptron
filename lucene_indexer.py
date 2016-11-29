#!/usr/bin/env Python2.7

#based on the example code at
#http://graus.nu/blog/pylucene-4-0-in-60-seconds-tutorial/

import sys
import lucene
 
from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, IntField, StringField, TextField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version

LUCENE_TYPES={'i':IntField,'s':StringField,'t':TextField}

 
if __name__ == "__main__":
  lucene.initVM()
  indexDir = SimpleFSDirectory(File("data/lucene_full_v1/"))
  writerConfig = IndexWriterConfig(Version.LUCENE_4_10_1, StandardAnalyzer())
  writer = IndexWriter(indexDir, writerConfig)
 
  print "%d docs in index" % writer.numDocs()
  print "Reading lines from sys.stdin..."
  header=[]
  for n, l in enumerate(sys.stdin):
    doc = Document()
    fields = l.rstrip().split("\t")
    #add one more field to header field set, which will index the concatenated set of all fields for general searches
    all_ = []
    if len(fields) < 1 or len(fields[0]) == 0:
        continue
    for (idx,field) in enumerate(fields):
        if n == 0:
            typechar = field[-1]
            if typechar not in set(['t','s','i']):
                sys.stderr.write("unexpected type char in last character position of header field: %s\n" % (field))
                exit(-1) 
            header.append([field,LUCENE_TYPES[typechar]])
        else:
            all_.append(field)
            (fname,fieldtype) = header[idx]
            if fieldtype is IntField:
                #sys.stdout.write("int field %s:%s\n" % (fname,field))
                field = int(field)
            doc.add(fieldtype(fname, field, Field.Store.YES))  #Field.Store.YES, Field.Index.ANALYZED))
            #doc.add(Field(fieldtype, field, Field.Store.YES, Field.Index.ANALYZED))
            #doc.add(fieldtype(header[idx][1],field,Field.Store.YES)
    if n > 0:
        all_fields = ' '.join(all_)
        doc.add(TextField('all_t', all_fields, Field.Store.NO))
    writer.addDocument(doc)
  print "Indexed %d lines from stdin (%d docs in index)" % (n, writer.numDocs())
  print "Closing index of %d docs..." % writer.numDocs()
  writer.close()

