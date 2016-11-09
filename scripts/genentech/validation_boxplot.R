mg <- read.table('genetech_novel_exons.results_gtex.shared.tsv', sep='\t', header=T)
ms <- read.table('genetech_novel_exons.results_srav2.shared.tsv', sep='\t', header=T)
mg$validated_by_resequencing <- factor(mg$validated_by_resequencing,labels=c('Did not validate', 'Validated'))
ms$validated_by_resequencing <- factor(ms$validated_by_resequencing,labels=c('Did not validate', 'Validated'))

par(mfrow=c(1,2))

boxplot(mg$all_shared_samples_count ~ mg$validated_by_resequencing, main="GTEx", ylab="Intropolis score")
tg <- wilcox.test(mg$all_shared_samples_count ~ mg$validated_by_resequencing, alternative="less")
tgp <- paste(c("pval",round(tg$p.value,digits=4)), collapse="")
text(1.5, 8500, tgp)

boxplot(ms$all_shared_samples_count ~ ms$validated_by_resequencing, main="SRAv2", ylab="Intropolis score")
ts <- wilcox.test(ms$all_shared_samples_count ~ ms$validated_by_resequencing, alternative="less")
tsp <- paste(c("pval",round(ts$p.value,digits=6)), collapse="")
text(1.5, 20500, tsp)
