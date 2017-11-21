import json
import os
import os.path as path

import numpy as np
from sklearn import preprocessing
from sklearn.externals import joblib
from sklearn.model_selection import KFold
import commonUtils
import lowLevelFeatures as ll
import validation
from validation import callChordino, callMusOOEvaluatorForFileList, extractMusOOAverageScore

def saveDatasetChroma(outfile, chromas,
    labels,
    kinds,
    mbids,
    start_times,
    durations):
    np.savez(
        outfile,
        chromas=chromas,
        labels=labels,
        kinds=kinds,
        mbids=mbids,
        start_times=start_times,
        durations=durations)

def loadDatasetChroma(infile):
    az = np.load(infile)
    return az['chromas'], az['labels'], az['kinds'], az['mbids'], az['start_times'], az['durations']

def chordLogProbabilities(amodel, chromaSegments):
    probs = np.zeros((len(chromaSegments.startTimes), 60))
    amaj=amodel[0]
    amin=amodel[1]
    adom=amodel[2]
    ahdim7=amodel[3]
    adim=amodel[4]
    chromas = chromaSegments.chromas
    for basePitch in range(12):
        pos = basePitch * 5
        # TODO: class
        #probs[:, pos] = amaj.score_samples(decimatedChroma)
        #probs[:, pos + 1] = amin.score_samples(decimatedChroma)
        #probs[:, pos + 2] = adom.score_samples(decimatedChroma)
        #probs[:, pos + 3] = ahdim7.score_samples(decimatedChroma)
        #probs[:, pos + 4] = adim.score_samples(decimatedChroma)
        d11Chroma = normalizeTo11d(chromas)
        probs[:, pos] = amaj.score_samples(d11Chroma)
        probs[:, pos + 1] = amin.score_samples(d11Chroma)
        probs[:, pos + 2] = adom.score_samples(d11Chroma)
        probs[:, pos + 3] = ahdim7.score_samples(d11Chroma)
        probs[:, pos + 4] = adim.score_samples(d11Chroma)
        chromas = np.roll(chromas, -1, axis=1)
    return  probs

def smoothProbabilities(p, degree):
    m = 1.0 / len(p)
    res = np.zeros(len(p), dtype='float')
    for i in xrange(len(p)):
        delta = m - p[i]
        if (delta > 0) :
            res[i] = p[i] + np.abs(delta) ** degree
        elif (delta < 0) :
            res[i] = p[i] - np.abs(delta) ** degree
        else :
            res[i] = p[i]
    return res/sum(res)


def callJazz(jazz_dir, jazz_ext, audioInFile, name):
    if not os.path.exists(jazz_dir):
        os.mkdir(jazz_dir)
    oursFile = os.path.join(jazz_dir, name + "." + jazz_ext)
    # TODO: class
    chordBeats(path.realpath(audioInFile), path.realpath(oursFile), smoothingTime=2.75)
    return oursFile

def indicesOfElementsIn(array, set):
    return [i for i,x in enumerate(array) if x in set]

class MBIDAwareKFold:
    mbidKFold = KFold()
    def __init__(self, n_splits = 5, random_state = 8):
        self.mbidKFold = KFold(
            n_splits = n_splits,
            shuffle = True,
            random_state = random_state)

    def split(self, mbids):
        mbidSet = set(mbids);
        uniqueMBIDs = np.array(list(mbidSet))
        for train_index, test_index in self.mbidKFold.split(uniqueMBIDs):
            trainMBIDs = set(uniqueMBIDs[train_index])
            testMBIDs = set(uniqueMBIDs[test_index])
            trainOrig = indicesOfElementsIn(mbids, trainMBIDs)
            testOrig = indicesOfElementsIn(mbids, testMBIDs)
            yield trainOrig, testOrig

def imputeZeros(data):
    data[data == 0] = 0.0001
    return data

def toLogRatio(chromaVector):
    res = np.zeros(11)
    product = 1.0
    for i in range(11):
        product = product * chromaVector[i]
        ii = i + 1.0
        res[i] = np.sqrt(ii / (ii + 1)) * np.log(product ** (1.0 / ii) / chromaVector[i + 1])
    return res

def normalizeTo11d(chromas) :
    c = preprocessing.normalize(imputeZeros(chromas), norm='l1')
    c = np.apply_along_axis(toLogRatio, 1, chromas)
    return c

def chordBeats(infile, outfile, smoothingTime=2.75) :
    thisPath = os.path.dirname(os.path.realpath(__file__))
    # TODO: class
    #amodel = joblib.load(os.path.join(thisPath, 'gmm100.pkl'))
    amodel = joblib.load(os.path.join(thisPath, 'gauss275log-ratio-sphere.pkl'))
    # TODO: class
    #chroma = normalizeTo11d(chroma)
    #noteNames = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab"]
    noteNames = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    chordNames = np.empty(60, dtype='object')
    for i in xrange(12):
        p = i * 5
        chordNames[p] = noteNames[i]
        chordNames[p + 1] = noteNames[i] + ":min"
        chordNames[p + 2] = noteNames[i] + ":7"
        chordNames[p + 3] = noteNames[i] + ":hdim7"
        chordNames[p + 4] = noteNames[i] + ":dim"
    beatSegments = ll.rnnBeatSegments(infile)
    chromaSegments = ll.loadNNLSChromas(
        path.realpath(infile),
        2048,
        smoothingTime,
        44100,
        beatSegments.startTimes,
        beatSegments.durations)
    probs = chordLogProbabilities(amodel, chromaSegments)

    # No HMM so far...
    indices = np.argmax(probs, axis=1)
    syms = map(lambda x: chordNames[x], indices)
    s = probs[xrange(len(indices)), indices]
    strengths = np.exp(s)
    strengths[s == 0] = 0
    duration = ll.audioDuration(path.realpath(infile))
    segments = commonUtils.toMirexLab(0.0, duration, beatSegments, syms, strengths)
    with open(outfile, 'w') as content_file:
        for s in segments:
            content_file.write(str(s) + '\n')
    return
    #indices = np.argmax(probs, axis=1)
    #
    #transitionMatrix = np.ones((24, 24)) * 1.0/24
    #logMatrix = np.log(transitionMatrix)
    #penalty = np.ones((24, 24)) * 0.15
    #penalty[xrange(24), xrange(24)] = 0
    #logMatrix = logMatrix - penalty
    #

    # temperley
    pOthers = np.array([
        113, 113, 1384, 1384, 410, 410, 326, 326, 2266, 2266, 20, 20, 2220, 2220, 412, 412, 454, 454, 1386, 1386,
         162, 162], dtype='float')
    pOthers = pOthers / sum(pOthers)
    pSelftransition = 5.0/8.0
    pModeChange = 1.0/24.0
    pMaj = np.concatenate((np.array([pSelftransition, pModeChange]), pOthers * (1.0 - pSelftransition - pModeChange)))
    pMin = np.concatenate((np.array([pModeChange, pSelftransition]), pOthers * (1.0 - pSelftransition - pModeChange)))
    pMaj = smoothProbabilities(pMaj, 1.055)
    pMin = smoothProbabilities(pMin, 1.055)
    transitionMatrix = np.zeros((24, 24))
    for i in xrange(12):
        transitionMatrix[2 * i, :] = np.roll(pMaj, 2 * i)
        transitionMatrix[2 * i + 1, :] = np.roll(pMin, 2 * i)
    #
    #
    #transitionMatrix = np.ones((24, 24), dtype='float') * 1.0/24

    # simplest one.
    #p = 0.046
    #transitionMatrix = np.ones((24, 24)) * (1 - p) / 24
    #transitionMatrix[xrange(24), xrange(24)]=p

    logMatrix = np.log(transitionMatrix)
    indices = viterbi(probs, logMatrix)
    syms = map(lambda x: chordNames[x], indices)
    segments = chordUtils.toBeatChordSegments(0.0, l / 44100.0, beats, syms)
    #chords = ChordsDetection(windowSize=0.2)
    #syms, strengths = chords(chroma)
    #endTime = l / 44100.0
    #stamps = np.arange(0, endTime, float(2048/44100.0))
    #segments = essentia_chord_utils.toMirexLab(0.0, endTime, stamps, syms, strengths)
    with open(outfile, 'w') as content_file:
        for s in segments:
            content_file.write(str(s) + '\n')



