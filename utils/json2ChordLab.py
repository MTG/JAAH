import sys
from chordUtils import json2lab
import argparse

def get_args():
    parser = argparse.ArgumentParser(
        description='convert input .json file to SonicVisualizer readable .lab file')
    parser.add_argument(
        '-i', '--input', type=str, help='input annotation file in .json file', required = True)
    parser.add_argument(
        '-o', '--output', type=str, default='output.lab', help='output file in .lab file (default output.lab)', required = True)
    args = parser.parse_args()
    infile = args.input
    outfile = args.output 
    
    return infile, outfile

try:
    infile, outfile = get_args()
    
except:
    print "usage:", sys.argv[0], "<input json file> <output lab file>"
    sys.exit()
    
 
    
json2lab(infile, outfile)
