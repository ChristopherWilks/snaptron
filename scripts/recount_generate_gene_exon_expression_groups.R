#run the gene-level coverage summarization code lifted in part from:
#https://github.com/leekgroup/recount-website/blob/master/rse/create_rse.R#L539
#and
#https://github.com/leekgroup/recount-website/blob/master/genes/create_bed.R#L12-L14


.load_install <- function(pkg, quietly = TRUE) {
  attemptName <- requireNamespace(pkg, quietly = quietly)
  if(!attemptName) {
    biocLite <- NULL ## To satisfy R CMD check
    
    source('http://bioconductor.org/biocLite.R')
    attemptInstall <- tryCatch(biocLite(pkg, suppressUpdates = quietly),
                               warning = function(w) 'failed')
    if(attemptInstall == 'failed') stop(paste('Failed to install', pkg))
    attemptName <- requireNamespace(pkg, quietly = quietly)
  }
  if(attemptName) {
    if(quietly) {
      suppressPackageStartupMessages(library(package = pkg,
                                             character.only = TRUE))
    } else {
      library(package = pkg, character.only = TRUE)
    }
  }
  return(invisible(NULL))
}


reproduce_ranges <- function(level = 'both', db = 'Gencode.mm.v15') {
  ## Check input
  level <- tolower(level)
  stopifnot(level %in% c('gene', 'exon', 'both'))
  stopifnot(db %in% c('Gencode.v25', 'EnsDb.Hsapiens.v79','Gencode.mm.v15'))
  
  
  
  ## Load required packages
  .load_install('GenomicFeatures')
  if (db == 'Gencode.v25') {
    txdb <- GenomicFeatures::makeTxDbFromGFF('ftp://ftp.sanger.ac.uk/pub/gencode/Gencode_human/release_25/gencode.v25.annotation.gff3.gz',
                                             format = 'gff3', organism = 'Homo sapiens')
  } else if(db == 'EnsDb.Hsapiens.v79') {
    .load_install('EnsDb.Hsapiens.v79')
    txdb <- EnsDb.Hsapiens.v79::EnsDb.Hsapiens.v79
  } else if(db == 'Gencode.mm.v15') {
    txdb <- GenomicFeatures::makeTxDbFromGFF('ftp://ftp.sanger.ac.uk/pub/gencode/Gencode_mouse/release_M15/gencode.vM15.basic.annotation.gff3.gz',
                                             format = 'gff3', organism = 'Mus musculus')
  }
  
  ## Get genes with default option single.strand.genes.only = TRUE
  genes <- GenomicFeatures::genes(txdb)
  
  ## Get Exons
  exons <- GenomicFeatures::exonsBy(txdb, by = 'gene')
  
  ## Keep only exons for gene ids that we selected previously
  if(!all(names(exons) %in% names(genes))) {
    warning('Dropping exons with gene ids not present in the gene list')
    exons <- exons[names(exons) %in% names(genes)]
  }
  
  ## Disjoin exons by gene so the exons won't be overlapping each other inside a gene
  exons <- GenomicRanges::disjoin(exons)
  
  if(level == 'exon') return(exons)
  
  ## For 'gene' or 'both', continue by:
  ## * adding length of disjoint exons by gene
  genes$bp_length <- sum(GenomicRanges::width(exons))
  
  ## * adding gene symbol
  #.load_install('org.Hs.eg.db')
  #.load_install('org.Mm.eg.db')
  if(db == 'Gencode.v25') {
    gene_info <- AnnotationDbi::mapIds(org.Hs.eg.db::org.Hs.eg.db,
                                       gsub('\\..*', '', names(genes)), 'SYMBOL', 'ENSEMBL',
                                       multiVals = 'CharacterList')
  } else if(db == 'EnsDb.Hsapiens.v79') {
    gene_info <- AnnotationDbi::mapIds(org.Hs.eg.db::org.Hs.eg.db,
                                       names(genes), 'SYMBOL', 'ENSEMBL', multiVals = 'CharacterList')
  } else if(db == 'Gencode.mm.v15') {
    gene_info <- AnnotationDbi::mapIds(org.Mm.eg.db::org.Mm.eg.db,
                                       gsub('\\..*', '', names(genes)), 'SYMBOL', 'ENSEMBL',
                                       multiVals = 'CharacterList')
  }
  genes$symbol <- gene_info
  
  if(level == 'gene') {
    return(genes)
  } else if (level == 'both') {
    return(list('exon' = exons, 'gene' = genes))
  }
}

source("https://bioconductor.org/biocLite.R")
biocLite("org.Hs.eg.db")
biocLite("org.Mm.eg.db")
library(GenomicRanges)
library("org.Mm.eg.db")
library("org.Hs.eg.db")
mexons<-reproduce_ranges(level='exon')
save(mexons,file="mouse_exons_gencodev15.Rdata")
library('rtracklayer')
export(unlist(mexons), con = 'Gencode-mm-v15.exons.bed', format='BED')

## Save how the exons are related, for speeding up the tsv -> count matrix step
## Group counts by gene
n <- elementNROWS(mexons)
count_groups <- rep(seq_len(length(n)), n)
cg<-as.matrix(count_groups)
rownames(cg)<-rep(names(n), n)
write.table(cg,file="./mouse_count_groups.tsv",quote=FALSE,sep="\t",col.names=FALSE)

###now do the BWtool runs against the BigWigs here, and then load in the summed file
#look at:
#https://github.com/leekgroup/recount-website/blob/master/generate_sums.sh
#and
#https://github.com/leekgroup/recount-website/blob/master/sum.sh


#the following is DEPRECATED
#use summarize_disjoint_exon_counts_to_gene_level.py instead to do the counts per gene summary
#now get gene expression counts summed over the disjoint exons
tsvFile<-'/home-1/cwilks3@jhu.edu/work/jling/gene_expression/coverage/all_disjoint_exon_expression_counts.tsv'
disjoint_exon_exp <- read.table(tsvFile, header = FALSE, colClasses = list('character', 'numeric', 'numeric', 'numeric'))

#convert "chr" columns to numeric (skipping the chr,start, and end columns)
d1<-apply(disjoint_exon_exp[4:ncol(disjoint_exon_exp)],2,as.numeric)

## Summarize counts at gene level
counts_gene <- lapply(split(as.data.frame(as.matrix(d1)), count_groups), colSums)
counts_gene <- do.call(rbind, counts_gene)
rownames(counts_gene) <- names(mexons)

#load samples metadata to get rail_id
samples<-read.table("./samples.tsv",sep="\t",header=TRUE,quote="",colClasses="character",comment.char="",check.names=FALSE)
colnames(counts_gene) <- t(samples['rail_id'])

#remember to bump the header column over by 1 on the output file
cg2<-format(counts_gene,scientific = FALSE)
write.table(counts_gene,file="./supermouse_gene_coverage.tsv",sep="\t",quote=FALSE)
