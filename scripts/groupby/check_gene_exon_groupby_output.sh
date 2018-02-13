head -1 /data?/*${1}*genes | cut -f 1 | grep "ENSG" | sort -u > genes_head
tail -n1 /data?/*${1}*genes | cut -f 1 | grep "ENSG" | sort -u > genes_tail
fgrep -f genes_head genes_tail
find /data? -name "*tcga*err" -size 0 -exec ls -l {} \; | wc -l
head -2 x??.map | grep "ENSG" | cut -d':' -f 1 | sort -u > expected_genes_head
tail -n1 x??.map | cut -d':' -f 1 | sort -u > expected_genes_tail
comm -1 -2 expected_genes_head genes_head | wc -l
comm -1 -2 expected_genes_tail genes_tail | wc -l
