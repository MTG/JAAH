import sys

try:
    infile = sys.argv[1]
    outfile = sys.argv[2]
except:
    print "usage:", sys.argv[0], "<input beats file> <output beats file>"
    sys.exit()

with open(infile, 'r') as ifile:
    lines = ifile.readlines()
    lines = map(str, map(float, map(str.strip, lines)))
    with open(outfile, 'w') as ofile:
        for i in xrange(0, len(lines), 16):
            ofile.write(", ".join(lines[i:i+16]) + ",\n")

