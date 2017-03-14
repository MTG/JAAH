import sys
from chordUtils import json2lab

try:
    infile = sys.argv[1]
    outfile = sys.argv[2]
except:
    print "usage:", sys.argv[0], "<input json file> <output lab file>"
    sys.exit()
json2lab(infile, outfile)
