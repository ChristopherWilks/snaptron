#!/usr/bin/env Rscript
infile <- file("stdin")
ts<-read.delim(infile)
groups<-levels(unique(ts$group))
for(group in groups)
{
	ts_single<-ts[ts$group == group,]
	p1<-kruskal.test(shared ~ tissue, data=ts_single)
	write(paste(c(group,p1$p.value),collapse="\t"),stdout())
}
