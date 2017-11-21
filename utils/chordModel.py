import lowLevelFeatures as ll
import numpy as np
import joblib
from sklearn import preprocessing
from sklearn.mixture import GaussianMixture
import os.path as path
import os

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

######################################################################
# Utility functions
######################################################################

def substituteZeros(chromas):
    data = np.copy(chromas)
    data[data == 0] = 0.0001
    return data

def toLogRatio(chromaVector) :
    res = np.zeros(len(chromaVector) - 1)
    product = 1.0
    for i in xrange(len(chromaVector) - 1):
        product = product * chromaVector[i]
        ii = i + 1.0
        res[i] = np.sqrt(ii / (ii + 1)) * np.log( product ** (1.0/ii) / chromaVector[i + 1])
    return res

def removeUnclassified(chromaSegments):
    return ll.AnnotatedChromaSegments(
        chromaSegments.labels[chromaSegments.kinds != 'unclassified'],
        chromaSegments.kinds[chromaSegments.kinds != 'unclassified'],
        chromaSegments.chromas[chromaSegments.kinds != 'unclassified'],
        chromaSegments.mbids[chromaSegments.kinds != 'unclassified'],
        chromaSegments.startTimes[chromaSegments.kinds != 'unclassified'],
        chromaSegments.durations[chromaSegments.kinds != 'unclassified'])

def viterbiStep(logProbs, logMatrix):
    newLogProbs = np.zeros(len(logProbs))
    bestIndices = np.zeros(len(logProbs), dtype='int')
    for i in xrange(len(logProbs)):
        pathLogProbs = logProbs + logMatrix[:, i]
        p = np.argmax(pathLogProbs)
        newLogProbs[i] = pathLogProbs[p]
        bestIndices[i] = p
    return newLogProbs, bestIndices


def viterbi(trellis, logMatrix):
    paths = np.zeros(trellis.shape, dtype='int')
    s = trellis[0,:]
    for i in xrange(1, trellis.shape[0]):
        s, prev = viterbiStep(s, logMatrix)
        paths[i, :] = prev
        s = s + trellis[i,:]
    best = np.empty(trellis.shape[0], dtype='int')
    strength = np.empty(trellis.shape[0], dtype='float')
    p = np.argmax(s)
    for i in xrange(trellis.shape[0] - 1, -1, -1):
        best[i] = p
        strength[i] = np.exp(trellis[i,p])
        p = paths[i, p]
    return best, strength

class ChordSegment :
    startTime = 0.0
    endTime = 0.0
    symbol = ''
    def __init__(self, startTime, endTime, symbol):
        self.startTime = startTime
        self.endTime = endTime
        self.symbol = symbol
    def __repr__(self):
        return str(self.startTime) + '\t' + str(self.endTime) + '\t' + self.symbol

def mergeSegments(chordSegments) :
    if (len(chordSegments) < 2) :
        return chordSegments
    res = []
    currentSegment = chordSegments[0]
    for segment in chordSegments[1:] :
        if (segment.symbol == currentSegment.symbol):
            currentSegment.endTime = segment.endTime
        else:
            res.append(currentSegment)
            currentSegment = segment
    res.append(currentSegment)
    return res

def toMirexLab(startTime, endTime, beatSegments, symbols, strengths) :
    if (len(beatSegments.startTimes) < len(symbols) or len(symbols) != len(strengths)) :
        raise ValueError("inappropriate lists lengths")
    res = []
    if (startTime < beatSegments.startTimes[0]) :
        res.append(ChordSegment(startTime, beatSegments.startTimes[0], 'N'))
    for i in xrange(len(symbols)) :
        sym = symbols[i] if strengths[i] > 0 else 'N'
        res.append(ChordSegment(
            beatSegments.startTimes[i],
            beatSegments.startTimes[i] + beatSegments.durations[i],
            sym))
    if (res[-1].endTime < endTime) :
        res.append(ChordSegment(res[-1].endTime, endTime, 'N'))
    return mergeSegments(res)

######################################################################
# Models
######################################################################

class ChordEmissionProbabilityModel:
    def __init__(self):
        return

    def logProbabilities(self, chromas):
        return np.zeros((len(chromas), N_CHORDS))

    def kindsForCRooted(self, cRootedChroma):
        return np.repeat('dom', len(cRootedChroma))

    def mirexChords(self, chromas):
        indices = np.argmax(self.logProbabilities(chromas))
        return map(lambda x: CHORD_NAMES[x], indices)

    def saveModel(self, fileName):
        joblib.dump(self, fileName)

    def fit(self, annotatedChromaSegments):
        return

class BasicGMMParameters:
    def __init__(
            self,
            norm=None,
            preprocessing=None,
            nComponents=np.ones(N_CHORD_KINDS, dtype=int),
            covarianceTypes=np.repeat('spherical', N_CHORD_KINDS)):
        """
        Parameters
        ----------
        norm : 'l1', 'l2', 'max', or None
        The norm to use to normalize each non zero sample.

        preprocessing: 'log', 'log-ratio' or None.

        nComponents : numpy array of length of N_CHORD_KINDS. Contains number of GMM
        components for each chord type: maj, min, dom, hdim7, dim.

        covarianceTypes : numpy array of length of N_CHORD_KINDS. Containns covariance
        tyope for each chord's GMM (see sklearn.mixture.GaussianMixture params).
        Elements are from the set: {'full', 'tied', 'diag', 'spherical'}.
        """
        self.norm = norm
        self.preprocessing = preprocessing
        self.nComponents = nComponents
        self.covarianceTypes = covarianceTypes

    def __str__(self):
        return ' norm: ' + str(self.norm) + \
               ' preprocessing: ' + str(self.preprocessing) + \
               ' nComponents: ' + str(self.nComponents) + \
               ' covarianceTypes: ' + str(self.covarianceTypes)

class BasicChordGMM(ChordEmissionProbabilityModel):
    def __init__(self, basicGMMParameters, gmms):
        self.basicGMMParameters=basicGMMParameters
        self.gmms = gmms

    #def __getnewargs__(self):
    #    return (BasicChordGMM.__repr__(self),)

    def preprocess(self, originalChromas):
        chromas = originalChromas
        if (self.basicGMMParameters.preprocessing is not None):
            # log preprocessing requires to eliminate zeros.
            chromas = substituteZeros(chromas)
        if (self.basicGMMParameters.norm is not None):
            chromas = preprocessing.normalize(chromas, norm=self.basicGMMParameters.norm)
        if (self.basicGMMParameters.preprocessing == 'log'):
            chromas = np.log(chromas)
        elif (self.basicGMMParameters.preprocessing == 'log-ratio'):
            chromas = np.apply_along_axis(toLogRatio, 1, chromas)
        elif (self.basicGMMParameters.preprocessing is not None):
            raise ValueError("Wrong preprocessing method: " + self.basicGMMParameters.preprocessing)
        return chromas

    def fit(self, annotatedChromaSegments):
        for i in xrange(N_CHORD_KINDS):
            self.gmms[i].fit(self.preprocess(
                annotatedChromaSegments.chromas[
                    annotatedChromaSegments.kinds == CHORD_KINDS[i]]))

    def logProbabilities(self, chromas):
        lps = np.zeros((len(chromas), N_CHORDS))
        for basePitch in xrange(N_PITCH_CLASSES):
            pos = basePitch * 5
            # NOTE: log-ratio preprocessing should be applied to shifted
            # chroma, so we always do it inside loop.
            preChromas = self.preprocess(chromas)
            for kind in xrange(N_CHORD_KINDS):
                lps[:, pos + kind] = self.gmms[kind].score_samples(preChromas)
            chromas = np.roll(chromas, -1, axis=1)
        return lps

    def predictKindsForCRooted(self, cRootedChroma):
        scores = np.zeros((len(cRootedChroma), N_CHORD_KINDS))
        preChromas = self.preprocess(cRootedChroma)
        for kind in xrange(N_CHORD_KINDS):
            scores[:, kind] = self.gmms[kind].score_samples(preChromas)
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


# training workflow
def trainBasicChordGMM(
        chromaEvaluationParameters,
        basicGMMParameters,
        jsonListFile):
    chromaEvaluator = ll.AnnotatedChromaEvaluator(chromaEvaluationParameters)
    gmms = map(lambda x:
            GaussianMixture(
                n_components=basicGMMParameters.nComponents[x],
                covariance_type=basicGMMParameters.covarianceTypes[x],
                max_iter=200,
                random_state = 8), xrange(N_CHORD_KINDS))
    gmm = BasicChordGMM(basicGMMParameters, gmms)
    gmm.fit(chromaEvaluator.loadChromasForAnnotationFileList(jsonListFile))
    return gmm

class ChordEstimator:
    def __init__(self,
        chromaEvaluationParameters,
        chordEmissionProbabilityModel,
        transitionMatrix):
        self.chromaEvaluationParameters = chromaEvaluationParameters
        self.emissionModel = chordEmissionProbabilityModel
        self.logTransitionMatrix = np.log(transitionMatrix)

    def estimate(self, audioFile):
        infile = str(path.realpath(audioFile))
        beatSegments = ll.rnnBeatSegments(infile)
        chromaSegments = ll.loadNNLSChromas(
            infile,
            self.chromaEvaluationParameters.stepSize,
            self.chromaEvaluationParameters.smoothingTime,
            self.chromaEvaluationParameters.sampleRate,
            beatSegments.startTimes,
            beatSegments.durations)
        logProbs = self.emissionModel.logProbabilities(chromaSegments.chromas)
        # No HMM
        #indices = np.argmax(logProbs, axis=1)
        #syms = map(lambda x: CHORD_NAMES[x], indices)
        #s = logProbs[xrange(len(indices)), indices]
        #strengths = np.exp(s)
        #strengths[s == 0] = 0
        # HMM
        indices, strengths = viterbi(logProbs, self.logTransitionMatrix)
        syms = map(lambda x: CHORD_NAMES[x], indices)
        return beatSegments, syms, strengths

    def estimateToMIREXFile(self, audioFile, outfile):
        beatSegments, syms, strengths = self.estimate(audioFile)
        duration = ll.audioDuration(path.realpath(audioFile))
        segments = toMirexLab(0.0, duration, beatSegments, syms, strengths)
        with open(outfile, 'w') as content_file:
            for s in segments:
                content_file.write(str(s) + '\n')

def loadModel(filename):
    return joblib.load(filename)

def callJazz(chordEstimator, jazz_dir, audioInFile, name, jazz_ext = 'lab'):
    if not path.exists(jazz_dir):
        os.mkdir(jazz_dir)
    oursFile = os.path.join(jazz_dir, name + "." + jazz_ext)
    chordEstimator.estimateToMIREXFile(path.realpath(audioInFile), path.realpath(oursFile))
    return oursFile
