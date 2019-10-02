dir=$(dirname $0)

#junctions for vignette
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=CD99&header=0" | cut -f 2- > junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr19:45297955-45298142&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr19:45298223-45299810&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr19:45297955-45299810&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr1:1879786-1879786&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr1:1879903-1879903&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr1:9664595-9664595&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr1:9664759-9664759&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr6:32831148-32831148&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr6:32831182-32831182&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr4:20763023-20763023&header=0" | cut -f 2- >> junctions.tsv
curl "http://snaptron.cs.jhu.edu/gtex/snaptron?regions=chr4:20763098-20763098&header=0" | cut -f 2- >> junctions.tsv

export LC_ALL=C
sort -u junctions.tsv | sort -k2,2 -k3,3n -k4,4n | gzip > junctions.gz

#genes for vignette
curl "http://snaptron.cs.jhu.edu/gtex/genes?regions=CD99&header=0" | cut -f 2- | gzip > genes.gz

#exons for vignette
curl "http://snaptron.cs.jhu.edu/gtex/exons?regions=CD99&header=0" | cut -f 2- | gzip > exons.gz

for f in exons genes junctions ; do /bin/bash -x ${dir}/../deploy/rebuild_junctions.sh ${f}.gz ./ $f ; done
