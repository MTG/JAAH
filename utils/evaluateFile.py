import os
import json
import argparse
from commonUtils import json2lab
from validation import callChordino, callMusOOEvaluatorForSingleFile, extractMusOOAverageScore, callCrema
from validation import callMusOOEvaluatorForSingleFile
from chordUtils import extractMusOOAverageScore
import chordModel
import lowLevelFeatures as ll

utils_path = os.path.dirname(os.path.realpath(__file__))
data_root = os.environ['JAZZ_HARMONY_DATA_ROOT']

parser = argparse.ArgumentParser(
    description='Check annotation well-formedness. Set parameters to empty if want to ignore corresponding file generator.')

parser.add_argument('infile', type=argparse.FileType('r'), help='input json file')
parser.add_argument('--chords', default='5JazzFunctions', help='preset name for --chords parameter of MusOOEvaluator (https://github.com/MTG/MusOOEvaluator). Default is 5JazzFunctions.')
parser.add_argument('--truth_dir', default='evaluation', help='directory for ground truth chords files extracted from annotation.')
parser.add_argument('--truth_ext', default='lab', help='extension for ground truth chords files extracted from annotation.')
parser.add_argument('--chordino_dir', default='evaluation', help='directory for chordino automatic chords files.')
parser.add_argument('--chordino_ext', default='chordino.lab', help='extension for chordino automatic chords files.')
parser.add_argument('--jazz_dir', default='evaluation', help='directory for jazz automatic chords files.')
parser.add_argument('--jazz_ext', default='jazz.lab', help='extension for jazz automatic chords files.')
parser.add_argument('--crema_dir', default='evaluation', help='directory for crema automatic chords files.')
parser.add_argument('--crema_ext', default='crema.lab', help='extension for crema automatic chords files.')
parser.add_argument('--museval', default=False, action='store_true', dest='do_eval', help='Evaluate with MusOOEvaluator')

args = parser.parse_args()
infile = args.infile.name
chords = args.chords

truth_dir = args.truth_dir
truth_ext=args.truth_ext
chordino_dir = args.chordino_dir
chordino_ext = args.chordino_ext
jazz_dir = args.jazz_dir
jazz_ext = args.jazz_ext
crema_dir = args.crema_dir
crema_ext = args.crema_ext
do_eval = args.do_eval

if (truth_dir == '') :
    print "truth_dir can't be empty"
    raise

if (truth_ext == '') :
    print "truth_ext can't be empty"
    raise

if not os.path.exists(truth_dir):
    os.mkdir(truth_dir)

with open(infile) as json_file:
    audiofile = json.load(json_file)['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', data_root)

audio_basename = os.path.basename(audiofile)
audio_name, audio_ext = os.path.splitext(audio_basename)

basename = os.path.basename(infile)
name, ext = os.path.splitext(basename)
labfile = os.path.join(truth_dir, name + "." + truth_ext)
json2lab('chords', infile, labfile)

if (chordino_dir != '' and chordino_ext != ''):
    chordinoFile = callChordino(chordino_dir, audiofile, name, chordino_ext = chordino_ext)

    if (do_eval):
        chordsQualityFile, segmentationQualityFile = callMusOOEvaluatorForSingleFile(
            dir=chordino_dir,
            name = name,
            ext = chordino_ext,
            chords = chords,
            testFile=chordinoFile,
            refFile = labfile)
        accuracy = extractMusOOAverageScore(chordsQualityFile)
        #call(['cat', chordsQualityFile])
        #call(['cat', segmentationQualityFile])
        print "Chordino accuracy for ", name, ": ", accuracy, "%"

if (crema_dir != '' and crema_ext != ''):
    cremaFile = callCrema(crema_dir, audiofile, name, crema_ext = crema_ext)

    if (do_eval):
        chordsQualityFile, segmentationQualityFile = callMusOOEvaluatorForSingleFile(
            dir=crema_dir,
            name = name,
            ext = crema_ext,
            chords = chords,
            testFile=cremaFile,
            refFile = labfile)
        accuracy = extractMusOOAverageScore(chordsQualityFile)
        #call(['cat', chordsQualityFile])
        #call(['cat', segmentationQualityFile])
        print "Crema accuracy for ", name, ": ", accuracy, "%"

if (jazz_dir != '' and jazz_ext != ''):
    # our algorithm
    thisPath = os.path.dirname(os.path.realpath(__file__))
    estimator = chordModel.ChordEstimator(
        ll.ChromaEvaluationParameters(2048, 1.2),
        chordModel.loadModel(os.path.join(thisPath, 'gauss275log-ratio-sphere.pkl')),
        chordModel.TRIVIAL_TRANSITION_MATRIX)
    jazzFile = chordModel.callJazz(estimator, jazz_dir, jazz_ext, audiofile, name)

    if (do_eval):
        outfile = os.path.join(jazz_dir, name + "." + jazz_ext +".MirexMajMin.txt")
        chordsQualityFile, segmentationQualityFile = callMusOOEvaluatorForSingleFile(
            dir=jazz_dir,
            name = name,
            ext = jazz_ext,
            chords = chords,
            testFile=jazzFile,
            refFile = labfile)
        accuracy = extractMusOOAverageScore(chordsQualityFile)
        #call(['cat', chordsQualityFile])
        #call(['cat', segmentationQualityFile])
        print "'Jazz' accuracy for ", name, ": ", accuracy, "%"


