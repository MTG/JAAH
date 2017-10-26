import argparse
from subprocess import call
from chordUtils import evaluateFileList, callJazz

parser = argparse.ArgumentParser(
    description='Evaluate chord prediction accuracy on given file list')

parser.add_argument('infile', type=argparse.FileType('r'), help='txt input file (with list of json annotations)')
parser.add_argument('--chordino', default=False, action='store_true', dest='chordino', help='Evaluate Chordino')
parser.add_argument('--jazz', default=False, action='store_true', dest='jazz', help='Evaluate Jazz')

args = parser.parse_args()

listFile = args.infile.name

res = ""
if (args.chordino):
    accuracy = evaluateFileList(listFile)
    res = res + "\nChordino accuracy for the dataset:" + str(accuracy) + "%"

if (args.jazz):
    accuracy = evaluateFileList(
        listFile,
        eval_dir="tmp_jazz_evaluation",
        truth_dir="tmp_true_chords",
        nameListFile="tmp_names.txt",
        predictionFun=callJazz)
    res = res + "\nJazz accuracy for the dataset:" + str(accuracy) + "%"

call(['cat', listFile])
print res;