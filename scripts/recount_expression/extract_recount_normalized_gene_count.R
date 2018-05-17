#!/usr/bin/env Rscript

args = commandArgs(trailingOnly=TRUE)
library(recount)
#load('/data2/expression_snaptron/gtex/rse_gene.Rdata')
load(args[2])
rse<-scale_counts(rse_gene)
df1<-t(data.frame(assays(rse[args[1]])$counts))
write.table(df1,args[3])
