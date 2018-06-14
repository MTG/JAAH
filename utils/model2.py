import plots
import lowLevelFeatures as ll
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from sklearn import preprocessing
import matplotlib.pyplot as plt
from plots import degrees
import math
import chordModel
import numpy as np
import os
from scipy.stats import beta
import symbolicAnalysis
import validation
import joblib
from scipy.misc import logsumexp

FOLD_PATH = 'folds'

TRAIN_FILES_LIST_PATTERN = 'folds' + '/' + "trainFiles_{0}.txt"
TEST_FILES_LIST_PATTERN = 'folds' + '/' + "testFiles_{0}.txt"
MODEL_PATTERN = 'folds' + '/' + "model2_{0}.pkl"
#MATRIX_PATTERN = 'folds' + '/' + "matrix_{0}.pkl"
ALL_FILES='ready.txt'
PITCH_CLASS_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
CHORD_KINDS = ["maj", "min", "dom", "hdim7", "dim"]
CHORD_MIREX_KINDS = ["", ":min", ":7", ":hdim7", ":dim"]
CHORD_NAMES = np.empty(60, dtype='object')

for p in xrange(len(PITCH_CLASS_NAMES)):
    for c in xrange(len(CHORD_MIREX_KINDS)):
        CHORD_NAMES[p * 5 + c] = PITCH_CLASS_NAMES[p] + CHORD_MIREX_KINDS[c]

N_PITCH_CLASSES = len(PITCH_CLASS_NAMES)
N_CHORD_KINDS = len(CHORD_KINDS)
N_CHORDS = len(CHORD_NAMES)
TRIVIAL_TRANSITION_MATRIX = np.ones((N_CHORDS, N_CHORDS), dtype='float') / N_CHORDS

FOLD_NUMBERS = np.arange(1, 6, dtype="int")

class Model2(chordModel.ChordEmissionProbabilityModel):
    def __init__(self, partitions, betas):
        self.partitions = partitions
        self.betas=betas

    def preprocess(self, originalChromas):
        chromas = originalChromas
        chromas = chordModel.substituteZeros(chromas)
        #chromas = np.apply_along_axis(chordModel.ilr, 1, chromas)
        return chromas

    """
    TODO
    def fit(self, annotatedChromaSegments):
        for i in xrange(N_CHORD_KINDS):
            self.betas[i].fit(self.preprocess(
                annotatedChromaSegments.chromas[
                    annotatedChromaSegments.kinds == CHORD_KINDS[i]]))
    """

    def logProbabilities(self, chromas):
        lps = np.zeros((len(chromas), N_CHORDS))
        for basePitch in xrange(N_PITCH_CLASSES):
            pos = basePitch * 5
            # NOTE: log-ratio preprocessing should be applied to shifted
            # chroma, so we always do it inside loop.
            preChromas = self.preprocess(chromas)
            for kind in xrange(N_CHORD_KINDS):
                #6.70978%
                # cdf weak
                #lps[:, pos + kind] = np.log(np.ones(len(lps)) - self.betas[kind].cdf(np.sum(preChromas[:, self.partitions[kind]], axis=1)))
                # cdf strong
                #lps[:, pos + kind] = np.log(self.betas[kind].cdf(np.sum(preChromas[:, self.partitions[kind]], axis=1)))
                #:6.72008%
                # pdf
                lps[:, pos + kind] = np.log(self.betas[kind].pdf(np.sum(preChromas[:, self.partitions[kind]], axis=1)))
            chromas = np.roll(chromas, -1, axis=1)
        # normalize. TODO: rethink: is it really needed.
        normSum = logsumexp(lps, axis=1)
        return lps - normSum[:, np.newaxis]

    def predictKindsForCRooted(self, cRootedChroma):
        scores = np.zeros((len(cRootedChroma), N_CHORD_KINDS))
        preChromas = self.preprocess(cRootedChroma)
        for kind in xrange(N_CHORD_KINDS):
            scores[:, kind] = 1 - self.betas[kind].cdf(sum(preChromas[self.partitions[kind]]))
        indices = np.argmax(scores, axis=1)
        np_kinds = np.array(CHORD_KINDS)
        return np_kinds[indices]

    def mirexChords(self, chromas):
        indices = np.argmax(self.logProbabilities(chromas))
        np_names = np.array(CHORD_NAMES)
        return np_names[indices]

    def scoreKindsForCRooted(self, cRootedChroma):
        pkinds = self.predictKindsForCRooted(cRootedChroma.chromas)
        total = np.sum(pkinds == cRootedChroma.kinds)
        return float(total) / len(cRootedChroma.kinds)

def trainCV(trainingChromaParams):
    chromaEvaluator = ll.AnnotatedChromaEvaluator(trainingChromaParams)
    for f in FOLD_NUMBERS:
        chromas = chromaEvaluator.loadChromasForAnnotationFileListFile(TRAIN_FILES_LIST_PATTERN.format(f))
        betas = np.empty(N_CHORD_KINDS, dtype='object')
        partitions = np.empty(N_CHORD_KINDS, dtype='object')
        for k in xrange(N_CHORD_KINDS):
            chord = preprocessing.normalize(
                chordModel.substituteZeros(chromas.chromas[chromas.kinds == CHORD_KINDS[k]]), norm='l1')
            sortedDegrees = plots.sortedDegrees(chord, method='mean')
            #partition = [degrees.index(x) for x in sortedDegrees[0:len(sortedDegrees) / 2]]
            partition = [degrees.index(x) for x in sortedDegrees[0:7]]
            partitions[k] = partition
            a = plots.estimatePartition(partition, chord)
            params = beta.fit(a, floc=0, fscale=1)
            plt.hist(a, 60, normed=True)
            rv = beta(*params)
            betas[k] = rv
            #x = np.linspace(0, 1)
            #plt.plot(x, rv.pdf(x), lw=2)
            #plt.plot(x, rv.cdf(x), lw=2)
            #plt.show()
        model = Model2(partitions, betas)
        model.saveModel(MODEL_PATTERN.format(f))

def testCV(
        testingChromaParams,
        predictions_dir = "tmp_jazz_evaluation",
        truth_dir ="tmp_true_chords",
        nameListFile="tmp_names.txt"):
    if not os.path.exists(predictions_dir):
        os.mkdir(predictions_dir)
    if not os.path.exists(truth_dir):
        os.mkdir(truth_dir)
    try:
        os.remove(nameListFile)
    except OSError:
        pass
    for f in FOLD_NUMBERS:
        # TODO: make it part of crossvalidation!
        matrix = symbolicAnalysis.loadTransitionMatrix('matrix.npz')
        #for i in xrange(matrix.shape[0]):
        #    matrix[:, i] = chordUtils.smoothProbabilities(matrix[:, i], 1.0055)
        estimator = chordModel.ChordEstimator(
            testingChromaParams,
            chordModel.loadModel(MODEL_PATTERN.format(f)),
            matrix)
            #chordModel.TRIVIAL_TRANSITION_MATRIX)
        validation.writeTruthAndPredictionsToLab(
            TEST_FILES_LIST_PATTERN.format(f),
            truth_dir=truth_dir,
            predictions_dir=predictions_dir,
            resultFilesListToAppend=nameListFile,
            predictionFunction=
            lambda predictions_dir, audiofile, name: chordModel.callJazz(
                estimator, predictions_dir, audiofile, name))
    accuracyByFile, totalAccuracy = validation.callMusOOEvaluatorForEachFileInList(
        nameListFile,
        truth_dir,
        predictions_dir)
    chordinoAccuracyByFile, chordinoTotalAccuracy = validation.chordinoAccuracies(ALL_FILES)
    cremaAccuracyByFile, cremaTotalAccuracy = validation.cremaAccuracies(ALL_FILES)
    result = np.empty(len(accuracyByFile), dtype=[('name', object), ('jazz', float), ('chordino', float), ('crema', float), ('harmonic rhythm', float)])
    rhythmByName = symbolicAnalysis.harmonicRhythmForEachFileInList(ALL_FILES)
    pos = 0
    for key, value in accuracyByFile.items():
        result[pos] = (key, value, chordinoAccuracyByFile[key], cremaAccuracyByFile[key], rhythmByName[key])
        pos += 1
    for row in result:
        print row;
    print "\nJazz accuracy for the dataset:" + str(totalAccuracy) + "%"
    print "\nChordino accuracy for the dataset:" + str(chordinoTotalAccuracy) + "%"
    print "\nCrema accuracy for the dataset:" + str(chordinoTotalAccuracy) + "%"
    return result


# degrees by entropy split by two
# plot histogram and fit beta
trainCV(trainingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2))
testCV(testingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2))
