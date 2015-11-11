# snaptron
fast webservices based query tool for large sets of genomic features

uses two 3rd party tools:

1) Tabix
2) Apache Solr

to populate variously structured data sources:

a) intervals repo storing the base feature information (Tabix,Solr)
b) sample metadata (Solr,RAM)

1) is used for quick interval searching over the features and is the main repo for streaming
2) is used for quick searching over all the other fields as well as searching over the associated metadata (in a separate index at this point)

snaptron manually hashjoins across above sources and intelligently modifies the user's query to optimize the searching
