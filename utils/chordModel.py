import lowLevelFeatures as ll
import numpy as np
import joblib
from sklearn import preprocessing
from sklearn.mixture import GaussianMixture

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

    def __init__(
            self,
            basicGMMParameters,
            max_iter=200,
            random_state = 8):
        self.basicGMMParameters=basicGMMParameters
        self.gmms = map(lambda x:
            GaussianMixture(
                n_components=basicGMMParameters.nComponents[x],
                covariance_type=basicGMMParameters.covarianceTypes[x],
                max_iter=max_iter,
                random_state = random_state), xrange(N_CHORD_KINDS))
        self.gmms = map(lambda x:
            GaussianMixture(1), xrange(N_CHORD_KINDS))

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
    gmm = BasicChordGMM(basicGMMParameters)
    gmm.fit(chromaEvaluator.loadChromasForAnnotationFileList(jsonListFile))
    return gmm
