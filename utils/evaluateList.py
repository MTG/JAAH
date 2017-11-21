import argparse
from subprocess import call
from validation import evaluateFileList
import chordModel
import os
import lowLevelFeatures as ll

parser = argparse.ArgumentParser(
    description='Evaluate chord prediction accuracy on given file list')

parser.add_argument('infile', type=argparse.FileType('r'), help='txt input file (with list of json annotations)')
parser.add_argument('--chordino', default=False, action='store_true', dest='chordino', help='Evaluate Chordino')
parser.add_argument('--jazz', default=False, action='store_true', dest='jazz', help='Evaluate Jazz')

args = parser.parse_args()

listFile = args.infile.name

res = ""
if (args.chordino):
    accuracyByFile, totalAccuracy = evaluateFileList(listFile)
    res = res + "\nChordino accuracy for the dataset:" + str(totalAccuracy) + "%"

if (args.jazz):
    thisPath = os.path.dirname(os.path.realpath(__file__))
    estimator = chordModel.ChordEstimator(
        ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=3),
        chordModel.loadModel(os.path.join(thisPath, 'gauss275log-ratio-sphere.pkl')),
        chordModel.TRIVIAL_TRANSITION_MATRIX)
    accuracyByFile, totalAccuracy = evaluateFileList(
        listFile,
        eval_dir="tmp_jazz_evaluation",
        truth_dir="tmp_true_chords",
        nameListFile="tmp_names.txt",
        predictionFun=lambda jazz_dir, audiofile, name :
        chordModel.callJazz(estimator, jazz_dir, audiofile, name)
    )
    res = res + "\nJazz accuracy for the dataset:" + str(totalAccuracy) + "%"

call(['cat', listFile])
print res;