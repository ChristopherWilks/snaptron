import sys
import math

group_mapping = sys.argv[1]

rids2groups = {}
with open(group_mapping,"r") as fin:
    for line in fin:
        fields = line.rstrip().split('\t')
        group = fields[0]
        rids = fields[3].split(',')
        rids2groups.update({rid:group for rid in rids})

group_names = sorted(set(rids2groups.values()))
  
sys.stdout.write("gene\t%s\n" % ('\t'.join(group_names)))

group_pos = []
group_pos_len = 0
for line in sys.stdin:
    line = line.rstrip()
    fields = line.split('\t')
    if group_pos_len == 0:
        group_pos = [rids2groups[rid] for rid in fields[1:]]
        group_pos_len = len(group_pos)
        continue
    gene = fields[0]
    group_sums = {group:0.0 for group in group_names}
    group_counts = {group:0 for group in group_names}
    for (i,val) in enumerate(fields[1:]):
        group_name = group_pos[i]
        group_sums[group_name] += float(val)
        group_counts[group_name] += 1
    means = []
    for gname in group_names:
        if group_counts[gname] > 0:
            val = float(group_sums[gname]/group_counts[gname])
            if val >= 1:
                means.append("%.1f" % math.log(val))
                continue
        means.append("0.0")
    sys.stdout.write("%s\t%s\n" % (gene, '\t'.join(means)))
