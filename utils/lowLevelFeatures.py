import numpy as np
import json
import re
import chordUtils
import joblib
import os


######################################################################
# Cache management
######################################################################

def getCaheDir():
    if (os.environ.has_key('JAZZ_HARMONY_CACHE_DIR')):
        return os.environ['JAZZ_HARMONY_CACHE_DIR']
    else:
        return None

memory = joblib.Memory(cachedir=getCaheDir(), verbose=0)

def clearCache():
    memory.clear()

######################################################################
# Basic structures
######################################################################

class Beats:
    def __init__(self, startTimes, durations):
        self.startTimes = startTimes
        self.durations = durations


class ChromaSegments(Beats):
    def __init__(self, chromas, mbids, startTimes, durations):
        self.chromas = chromas
        self.mbids = mbids
        Beats.__init__(self, startTimes, durations)


class AnnotatedChromaSegments(ChromaSegments):
    def __init__(self, labels, kinds, chromas, mbids, startTimes, durations):
        self.labels = labels
        self.kinds = kinds
        ChromaSegments.__init__(self, chromas, mbids, startTimes, durations)


######################################################################
# Parameters
######################################################################

class BeatsFromAnnotationParameters:
    def __str__(self):
        return 'Beats from annotation'

class ChromaEvaluationParameters:
    def __init__(self,
               stepSize = 2048,
               smoothingTime = 1.3,
               beatsParameters = BeatsFromAnnotationParameters(),
               rollToCRoot = True):
        self.stepSize = stepSize
        self.smoothingTime = smoothingTime
        self.beatsParameters = beatsParameters
        self.rollToCRoot = rollToCRoot

    def __str__(self):
        return ' stepSize: ' + str(self.stepSize) +\
               ' smoothingTime: ' + str(self.smoothingTime) +\
               str(self.beatsParameters)


class FileChromaParameters:
    def __init__(self,
                 fileRef,
                 chromaParameters = ChromaEvaluationParameters()):
        self.fileRef = fileRef
        self.chromaParameters = chromaParameters

    def __str__(self):
        return str(self.fileRef) + str(self.chromaParameters)

######################################################################
# Loaders/Evaluators
######################################################################
pitches = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'B':11}
alt={'b':-1, '#':1}
shortcuts={'maj':'(3,5)', 'min':'(b3,5)', 'dim':'(b3,b5)', 'aug':'(3,#5)', 'maj7':'(3,5,7)',
'min7':'(b3,5,b7)', '7':'(3,5,b7)', 'dim7':'(b3,b5,bb7)', 'hdim7':'(b3,b5,b7)',
'minmaj7':'(b3,5,7)', 'maj6':'(3,5,6)', 'min6':'(b3,5,6)', '9':'(3,5,b7,9)',
'maj9':'(3,5,7,9)', 'min9':'(b3,5,b7,9)', 'sus4':'(4,5)'}

def toPitchAndKind(label):
    partsAndBass = label.split('/')
    parts = partsAndBass[0].split(':')
    note = parts[0]
    if (note[0] == 'N'):
        return 9, 'unclassified'
    pitch=pitches[note[0]]
    if (len(note) >= 2):
        for i in range(1, len(note)):
            pitch = pitch + alt[note[i]]
    if (len(parts) == 1) :
        kind = 'maj'
    else:
        kind = parts[1].split('/')[0]
    if (kind in shortcuts):
        kind = shortcuts[kind]
    degrees = set(re.sub("[\(\)]", "", kind).split(','))
    # TODO after the dataset is fixed (bass -> pitch class set).
    if (len(partsAndBass) > 1):
        degrees.add(partsAndBass[1])
    if ('3' in degrees):
        if ('b7' in degrees):
            kind='dom'
        else:
            kind='maj'
    elif ('b3' in degrees):
        if ('b5' in degrees):
            if ('b7' in degrees):
                kind='hdim7'
            else:
                kind='dim'
        else:
            kind='min'
    else:
        kind='unclassified'
    '''
    if ('3' in degrees and 'b7' in degrees):
        kind='dom'
    elif ('3' in degrees and not '#5' in degrees and not 'b5' in degrees and not '4' in degrees):
        kind='maj'
    elif ('b3' in degrees):
        if ('b5' in degrees and 'b7' in degrees):
            kind='hdim7'
        #elif ('b5' in degrees and 'bb7' in degrees):
        # TODO: discuss this questionable decision.
        elif ('b5' in degrees):
            kind = 'dim7'
        elif ('5' in degrees):
            kind = 'min'
        else:
            kind='unclassified'
    else:
        kind = 'unclassified'
    '''
    return pitch, kind

class AnnotatedChromaEvaluator:
    def __init__(self,
                 chromaEvaluationParameters = ChromaEvaluationParameters(),
                 sampleRate = 44100):
        self.chromaEvaluationParameters = chromaEvaluationParameters
        self.sampleRate = sampleRate

    # returns AnnotatedChromaSegments for the file list
    def loadChromasForAnnotationFileList(self, fileListFile):
        res = AnnotatedChromaSegments(
            labels=np.array([], dtype='object'),
            kinds=np.array([], dtype='object'),
            chromas=np.zeros((0,12), dtype='float32'),
            mbids=np.array([], dtype='object'),
            startTimes=np.array([], dtype='float32'),
            durations=np.array([], dtype='float32'))
        with open(fileListFile) as list_file:
            for line in list_file:
                chunk = self.loadChromasForAnnotationFile(line.rstrip())
                res.chromas = np.concatenate((res.chromas, chunk.chromas))
                res.labels = np.concatenate((res.labels, chunk.labels))
                res.kinds = np.concatenate((res.kinds, chunk.kinds))
                res.mbids = np.concatenate((res.mbids, chunk.mbids))
                res.startTimes = np.concatenate((res.startTimes, chunk.startTimes))
                res.durations = np.concatenate((res.durations, chunk.durations))
        return res

    def getAnnotatedFileChromaParameters(self, annotationFileName):
        return FileChromaParameters(
            annotationFileName,
            self.chromaEvaluationParameters)

    # returns AnnotatedChromaSegments for the file
    def loadChromasForAnnotationFile(
            self,
            annotationFileName):
        params = self.getAnnotatedFileChromaParameters(annotationFileName)
        return loadAnnotatedNNLSChromas(
            str(params.fileRef),
            params.chromaParameters.stepSize,
            params.chromaParameters.smoothingTime,
            params.chromaParameters.rollToCRoot,
            self.sampleRate)

@memory.cache
def loadAnnotatedNNLSChromas(
        jsonFileName,
        stepSize,
        smoothingTime,
        rollToCRoot,
        sampleRate):
    print memory
    with open(jsonFileName) as json_file:
        print json_file
        data = json.load(json_file)
        mbid = data['mbid']
        audiofile = data['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', chordUtils.getDataRoot())
        duration = data['duration']
        metreNumerator = int(data['metre'].split('/')[0])
        allBeats = []
        allChords = []
        chordUtils.processParts(metreNumerator, data, allBeats, allChords, 'chords')
        segments = chordUtils.toBeatChordSegments(0, duration, allBeats, allChords)
        #
        chroma, l = chordUtils.chromaFromAudio(
            audiofile,
            sampleRate=sampleRate,
            stepSize=stepSize,
            smoothingTime=smoothingTime)
        chromas = np.zeros((len(segments), 12), dtype='float32')
        labels = np.empty(len(segments), dtype='object')
        kinds = np.empty(len(segments), dtype='object')
        mbids = np.empty(len(segments), dtype='object')
        startTimes = np.zeros(len(segments), dtype='float32')
        durations = np.zeros(len(segments), dtype='float32')
        for i in range(len(segments)):
            pitch, kind = toPitchAndKind(segments[i].symbol)
            s = int(float(segments[i].startTime) *
                    sampleRate / stepSize)
            e = int(float(segments[i].endTime) *
                    sampleRate / stepSize)
            if (s == e):
                print "empty segment ", segments[i].startTime, segments[i].endTime
                raise
            # roll from 'A' based to 'C' based
            shift = -3
            if (rollToCRoot):
                shift -= pitch
            if (shift < 0):
                shift += 12
            chromas[i] = np.roll(chroma[s], shift=shift, axis=0)
            labels[i] = segments[i].symbol
            kinds[i] = kind
            mbids[i] = mbid
            startTimes[i] = segments[i].startTime
            durations[i] = float(segments[i].endTime) - float(segments[i].startTime)
        return AnnotatedChromaSegments(labels, kinds, chromas, mbids, startTimes, durations)
