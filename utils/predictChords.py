import chordUtils
import argparse

parser = argparse.ArgumentParser(description='Predict chords')

parser.add_argument('infile', type=argparse.FileType('r'), help='wav input file')
parser.add_argument('--output', '-o', type=argparse.FileType('w'), default='out.lab', help='output .lab file')

args = parser.parse_args()

infile = args.infile.name
outfile = args.output.name

args = parser.parse_args()

chordUtils.chordBeats(infile, outfile)
