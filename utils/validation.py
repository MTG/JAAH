import re
from subprocess import call

import numpy as np
import chordModel
import commonUtils
import os
import json
import cacher
import symbolicAnalysis
import lowLevelFeatures as ll
import matplotlib.pyplot as plt

FOLD_PATH = 'folds'

TRAIN_FILES_LIST_PATTERN = 'folds' + '/' + "trainFiles_{0}.txt"
TEST_FILES_LIST_PATTERN = 'folds' + '/' + "testFiles_{0}.txt"
MODEL_ILR__PATTERN = 'folds' + '/' + "model_{0}.pkl"
MODEL_ALR_PATTERN = 'folds' + '/' + "model_alr_{0}.pkl"
MODEL_CLR_PATTERN = 'folds' + '/' + "model_clr_{0}.pkl"
#MATRIX_PATTERN = 'folds' + '/' + "matrix_{0}.pkl"
ALL_FILES='ready.txt'

FOLD_NUMBERS = np.arange(1, 6, dtype="int")

def callChordino(chordino_dir, audioInFile, name, chordino_ext = 'lab'):
    audio_basename = os.path.basename(audioInFile)
    audio_name, audio_ext = os.path.splitext(audio_basename)
    # workaround for chordino bug.
    audio_name = audio_name.split('#')[0]
    if not os.path.exists(chordino_dir):
        os.mkdir(chordino_dir)
    utils_path = os.path.dirname(os.path.realpath(__file__))
    chordinoFile = os.path.join(chordino_dir, audio_name + "_vamp_nnls-chroma_chordino_simplechord.lab")
    call(["sonic-annotator",
          "-t", utils_path + "/chords.n3",
          "-w", "lab",
          "--lab-basedir",
          chordino_dir,
          "--lab-fill-ends",
          audioInFile])
    with open(chordinoFile, 'r') as content_file:
        content = content_file.read().replace('"', '')
        os.remove(chordinoFile)
        chordinoFile = os.path.join(chordino_dir, name + "." + chordino_ext)
        with open(chordinoFile, 'w') as content_file:
            content_file.write(content)
    return chordinoFile

def callCrema(crema_dir, audioInFile, name, crema_ext = 'lab'):
    audio_basename = os.path.basename(audioInFile)
    audio_name, audio_ext = os.path.splitext(audio_basename)
    # workaround for chordino bug.
    audio_name = audio_name.split('#')[0]
    if not os.path.exists(crema_dir):
        os.mkdir(crema_dir)
    utils_path = os.path.dirname(os.path.realpath(__file__))
    chordinoFile = os.path.join(crema_dir, name + "." + crema_ext)
    call([utils_path + "/run_crema.sh",
          audioInFile,
          crema_dir,
          name,
          crema_ext])
    return chordinoFile

def callMusOOEvaluatorForFileList(
        fileList, refdir, testdir, refext = 'lab', testext = 'lab', chords = '5JazzFunctions'):
    chordsFile = os.path.join(testdir, "accuracy." + chords + ".txt")
    call([
        'MusOOEvaluator',
        '--list', fileList,
        '--refdir', refdir,
        '--testdir', testdir,
        '--refext', "." + refext,
        '--testext', "." + testext,
        '--chords', chords,
        '--output', chordsFile])
    segmentationFile = os.path.join(testdir, "accuracy" + ".segmentation.txt")
    call([
        'MusOOEvaluator',
        '--list', fileList,
        '--refdir', refdir,
        '--testdir', testdir,
        '--refext', "." + refext,
        '--testext', "." + testext,
        '--segmentation', 'Inner',
        '--output', segmentationFile])
    return chordsFile, segmentationFile


def callMusOOEvaluatorForSingleFile(dir, name, ext, chords, testFile, refFile):
    chordsFile = os.path.join(dir, name + "." + ext + "." + chords + ".txt")
    call([
        'MusOOEvaluator',
        '--testfile', testFile,
        '--reffile', refFile,
        '--chords', chords,
        '--output', chordsFile])
    segmentationFile = os.path.join(dir, name + "." + ext + ".segmentation.txt")
    call([
        'MusOOEvaluator',
        '--testfile', testFile,
        '--reffile', refFile,
        '--segmentation', 'Inner',
        '--output', segmentationFile])
    return chordsFile, segmentationFile

def callMusOOEvaluatorForEachFileInList(
        fileList, refdir, testdir, chords = '5JazzFunctions'):
    resultByFile = {}
    with open(fileList) as list_file:
        for line in list_file:
            infile = line.rstrip()
            basename = os.path.basename(infile)
            name, jsonExt = os.path.splitext(basename)
            testFile = os.path.join(testdir, name + ".lab")
            refFile = os.path.join(refdir, name + ".lab")
            chordsFile, segmentationFile = callMusOOEvaluatorForSingleFile(
                testdir, name, 'lab', chords, testFile, refFile)
            resultByFile[name] = (chordsFile, segmentationFile)
    chordsFile, segmentationFile = callMusOOEvaluatorForFileList(
        fileList,
        refdir,
        testdir,
        chords = chords)
    totalAccuracy = extractMusOOAverageScore(chordsFile)
    accuracyByFile = {}
    for key, value in resultByFile.items():
        accuracyByFile[key] = extractMusOOAverageScore(value[0])
    return accuracyByFile, totalAccuracy


def extractMusOOAverageScore(scoreFile) :
    with open(scoreFile, 'r') as content_file:
        content = content_file.read()
        s = re.search("Average score: ([^%]*)%", content)
        return float(s.group(1))

def trainGMM_CV(trainingChromaParams, gmmParams, modelPattern=MODEL_ILR__PATTERN):
    for f in FOLD_NUMBERS:
        gmm = chordModel.trainBasicChordGMM(trainingChromaParams, gmmParams, TRAIN_FILES_LIST_PATTERN.format(f))
        gmm.saveModel(modelPattern.format(f))

def writeTruthAndPredictionsToLab(
        jsonList,
        truth_dir = "tmp_true_chords",
        predictions_dir="tmp_jazz_evaluation",
        resultFilesListToAppend="tmp_names.txt",
        predictionFunction = callChordino):
    data_root = commonUtils.getDataRoot()
    if not os.path.exists(predictions_dir):
        os.mkdir(predictions_dir)
    if not os.path.exists(truth_dir):
        os.mkdir(truth_dir)
    nf = open(resultFilesListToAppend, "a")
    with open(jsonList) as list_file:
        for line in list_file:
            infile = line.rstrip()
            basename = os.path.basename(infile)
            name, ext = os.path.splitext(basename)
            nf.write(name + "\n")
            labfile = os.path.join(truth_dir, name + ".lab")
            commonUtils.json2lab('chords', infile, labfile)
            with open(infile) as json_file:
                data = json.load(json_file)
                audiofile = data['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', data_root)
                predictionFunction(predictions_dir, audiofile, name)
    nf.close()

def evaluateFileList(
        jsonList,
        eval_dir = "tmp_chordino_evaluation",
        truth_dir = "tmp_true_chords",
        nameListFile="tmp_names.txt",
        predictionFunction =callChordino):
    writeTruthAndPredictionsToLab(
        jsonList,
        truth_dir=truth_dir,
        predictions_dir=eval_dir,
        resultFilesListToAppend=nameListFile,
        predictionFunction=predictionFunction)
    return callMusOOEvaluatorForEachFileInList(
        nameListFile,
        truth_dir,
        eval_dir)

@cacher.memory.cache
def chordinoAccuracies(jsonList):
    return evaluateFileList(jsonList)

@cacher.memory.cache
def cremaAccuracies(jsonList):
    return evaluateFileList(
        jsonList,
        eval_dir = "tmp_crema_evaluation",
        truth_dir = "tmp_true_chords",
        nameListFile="tmp_names.txt",
        predictionFunction =callCrema)

def testCV(
        testingChromaParams,
        predictions_dir = "tmp_jazz_evaluation",
        truth_dir ="tmp_true_chords",
        nameListFile="tmp_names.txt",
        modelPattern=MODEL_ILR__PATTERN):
    if not os.path.exists(predictions_dir):
        os.mkdir(predictions_dir)
    if not os.path.exists(truth_dir):
        os.mkdir(truth_dir)
    try:
        os.remove(nameListFile)
    except OSError:
        pass
    cremaAccuracyByFile, cremaTotalAccuracy = cremaAccuracies(ALL_FILES)
    chordinoAccuracyByFile, chordinoTotalAccuracy = chordinoAccuracies(ALL_FILES)
    for f in FOLD_NUMBERS:
        # TODO: make it part of crossvalidation!
        matrix = symbolicAnalysis.loadTransitionMatrix('matrix.npz')
        #for i in xrange(matrix.shape[0]):
        #    matrix[:, i] = chordUtils.smoothProbabilities(matrix[:, i], 1.0055)
        estimator = chordModel.ChordEstimator(
            testingChromaParams,
            chordModel.loadModel(modelPattern.format(f)),
            matrix)
            #chordModel.TRIVIAL_TRANSITION_MATRIX)
        writeTruthAndPredictionsToLab(
            TEST_FILES_LIST_PATTERN.format(f),
            truth_dir=truth_dir,
            predictions_dir=predictions_dir,
            resultFilesListToAppend=nameListFile,
            predictionFunction=
            lambda predictions_dir, audiofile, name: chordModel.callJazz(
                estimator, predictions_dir, audiofile, name))
    accuracyByFile, totalAccuracy = callMusOOEvaluatorForEachFileInList(
        nameListFile,
        truth_dir,
        predictions_dir)
    result = np.empty(len(accuracyByFile), dtype=[('name', object), ('jazz', float), ('chordino', float), ('crema', float), ('harmonic rhythm', float)])
    rhythmByName = symbolicAnalysis.harmonicRhythmForEachFileInList(ALL_FILES)
    pos = 0
    for key, value in accuracyByFile.items():
        result[pos] = (key, value, chordinoAccuracyByFile[key], cremaAccuracyByFile[key], rhythmByName[key])
        pos += 1
    #for row in result:
    #    print row;
    print "\nJazz accuracy for the dataset:" + str(totalAccuracy) + "%"
    print "\nChordino accuracy for the dataset:" + str(chordinoTotalAccuracy) + "%"
    print "\nCrema accuracy for the dataset:" + str(cremaTotalAccuracy) + "%"
    resultMap={}
    resultMap['tracks'] = result
    resultMap['jazz'] = totalAccuracy
    resultMap['chordino'] = chordinoTotalAccuracy
    resultMap['crema'] = cremaTotalAccuracy
    return resultMap

from sklearn.mixture import GaussianMixture

def estimateBICs(data, covariance_type='full', min_components=1, max_components=40):
    res = np.zeros(max_components - min_components + 1)
    for i in range(min_components, max_components + 1):
        gm = GaussianMixture(
            n_components=i, covariance_type=covariance_type,
            max_iter=200,
            random_state = 8)
        gm.fit(data)
        curBic = gm.bic(data)
        res[i - 1] = curBic
        if (not gm.converged_):
            print i, curBic, gm.converged_
    return res

def findOptimalNComponentsByBIC(trainingChromaParams, f = 1, min_components=1, max_components=30):
    # gmm = chordModel.trainBasicChordGMM(trainingChromaParams, gmmParams, TRAIN_FILES_LIST_PATTERN.format(f))
    #gmm.saveModel(modelPattern.format(f))
    fig, ax = plt.subplots(nrows=3,ncols=2)
    ax = np.reshape(np.array(ax), (1, np.size(ax)))[0]
    res = np.zeros(chordModel.N_CHORD_KINDS)
    segments = ll.AnnotatedChromaEvaluator(trainingChromaParams). \
        loadChromasForAnnotationFileListFile(TRAIN_FILES_LIST_PATTERN.format(f))
    for i in xrange(chordModel.N_CHORD_KINDS):
        chordname = chordModel.CHORD_KINDS[i]
        samples = segments.chromas[segments.kinds ==chordname]
        bics = estimateBICs(samples,\
                           min_components=min_components,\
                           max_components=min(max_components, len(samples)))
        ax[i].set_title(chordname)
        ax[i].plot(bics)
        minIndex = np.argmin(bics)
        print chordname, "BIC: ", bics[minIndex], " N: ", minIndex + 1
        res[i] = minIndex + 1
    plt.show()
    return res

########################################################################################

#Example
#trainGMM_CV(
#    trainingChromaParams = ll.ChromaEvaluationParameters(2048, 1.25),
#    gmmParams=chordModel.BasicGMMParameters(norm='l1', preprocessing='ilr'), covarianceTypes='diagonal')
#chordModel.N_CHORD_KINDS)))
#res = testCV(testingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2))

# BIC
#validation.findOptimalNComponentsByBIC(f=2,trainingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2))
#[ 20.,  16.,  25.,   4.,   4.]
# [17, 15, 18, 3, 5]
#validation.trainGMM_CV(
#    trainingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2),
#    gmmParams=chordModel.BasicGMMParameters(norm=None, preprocessing=None, nComponents=np.array([20, 20, 20, 3, 5]), covarianceTypes=np.repeat('full', chordModel.N_CHORD_KINDS)))
#res = validation.testCV(testingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2))
