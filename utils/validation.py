import numpy as np
import lowLevelFeatures as ll
import chordModel
import chordUtils
import os
import json

foldPath = 'folds'
trainListPattern = 'folds' + '/' + "trainFiles_{0}.txt"
testListPattern = 'folds' + '/' + "testFiles_{0}.txt"
modelPattern = 'folds' + '/' + "model_{0}.pkl"


FOLD_NUMBERS = np.arange(1, 6, dtype="int")

#TODO: 0.25..3.5 (4?) smoothing training/test +
# best training, varied testing/best testing/varied training
# for training - could be smaller (1.25) for testing - bigger.
trainingChromaParams = ll.ChromaEvaluationParameters(2048, 1.25)
testingChromaParams = ll.ChromaEvaluationParameters(2048, 3.5)
gmmParams = chordModel.BasicGMMParameters(norm='l1', preprocessing='log-ratio')

def train():
    for f in FOLD_NUMBERS:
        gmm = chordModel.trainBasicChordGMM(trainingChromaParams, gmmParams, trainListPattern.format(f))
        gmm.saveModel(modelPattern.format(f))

def test(
        eval_dir = "tmp_jazz_evaluation",
        truth_dir = "tmp_true_chords",
        nameListFile="tmp_names.txt"):
    data_root = chordUtils.getDataRoot()
    if not os.path.exists(eval_dir):
        os.mkdir(eval_dir)
    if not os.path.exists(truth_dir):
        os.mkdir(truth_dir)
    nf = open(nameListFile, "w")
    for f in FOLD_NUMBERS:
        estimator = chordModel.ChordEstimator(
            testingChromaParams,
            chordModel.loadModel(modelPattern.format(f)),
            chordModel.TRIVIAL_TRANSITION_MATRIX)
        with open(testListPattern.format(f)) as list_file:
            for line in list_file:
                infile = line.rstrip()
                basename = os.path.basename(infile)
                name, ext = os.path.splitext(basename)
                nf.write(name + "\n")
                labfile = os.path.join(truth_dir, name + ".lab")
                chordUtils.json2lab('chords', infile, labfile)
                with open(infile) as json_file:
                    data = json.load(json_file)
                    audiofile = data['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', data_root)
                    chordModel.callJazz(
                        estimator, eval_dir, "lab", audiofile, name)
    nf.close()
    chordsFile, segmentationFile = chordUtils.callMusOOEvaluatorForFileList(
        nameListFile,
        truth_dir,
        eval_dir)
    accuracy = chordUtils.extractMusOOAverageScore(chordsFile)
    print "\nJazz accuracy for the dataset:" + str(accuracy) + "%"

train()
test()


