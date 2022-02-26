import sys

for line in sys.stdin:
    if '?' in line:
        line = line.replace('?','*')
    sys.stdout.write("%s" % line)
