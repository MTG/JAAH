import essentia.standard
import numpy as np
import json
import re

import vamp
import madmom.features as mf
import os.path as path
import commonUtils
import cacher

######################################################################
# Basic structures
######################################################################

class BeatSegments:
    def __init__(self, startTimes, durations):
        self.startTimes = startTimes
        self.durations = durations


class ChromaSegments(BeatSegments):
    def __init__(self, chromas, startTimes, durations):
        self.chromas = chromas
        BeatSegments.__init__(self, startTimes, durations)


class AnnotatedChromaSegments(ChromaSegments):
    def __init__(self, labels, kinds, chromas, mbids, startTimes, durations):
        self.labels = labels
        self.kinds = kinds
        self.mbids = mbids
        ChromaSegments.__init__(self, chromas, startTimes, durations)

######################################################################
# Parameters
######################################################################

class ChromaEvaluationParameters:
    def __init__(self,
               stepSize = 2048,
               smoothingTime = 1.25,
               rollToCRoot = True,
               sampleRate = 44100):
        self.stepSize = stepSize
        self.smoothingTime = smoothingTime
        self.rollToCRoot = rollToCRoot
        self.sampleRate = sampleRate

    def __str__(self):
        return ' stepSize: ' + str(self.stepSize) +\
               ' smoothingTime: ' + str(self.smoothingTime) +\
               ' rollToCRoot: ' + str(self.rollToCRoot)+\
               ' sampleRate: ' + str(self.sampleRate)


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
UNCLASSIFIED = 'unclassified'

def noteToNumber(note):
    pitch=pitches[note[0]]
    if (len(note) >= 2):
        for i in range(1, len(note)):
            pitch = pitch + alt[note[i]]
    return pitch

def toPitchAndKind(label):
    partsAndBass = label.split('/')
    parts = partsAndBass[0].split(':')
    note = parts[0]
    if (note[0] == 'N'):
        return 9, 'unclassified'
    pitch = noteToNumber(note)
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
                 chromaEvaluationParameters = ChromaEvaluationParameters()):
        self.chromaEvaluationParameters = chromaEvaluationParameters

    def loadChromasForAnnotationFileList(self, fileList):
        res = AnnotatedChromaSegments(
            labels=np.array([], dtype='object'),
            kinds=np.array([], dtype='object'),
            chromas=np.zeros((0,12), dtype='float32'),
            mbids=np.array([], dtype='object'),
            startTimes=np.array([], dtype='float32'),
            durations=np.array([], dtype='float32'))
        for file in fileList:
            chunk = self.loadChromasForAnnotationFile(file)
            res.chromas = np.concatenate((res.chromas, chunk.chromas))
            res.labels = np.concatenate((res.labels, chunk.labels))
            res.kinds = np.concatenate((res.kinds, chunk.kinds))
            res.mbids = np.concatenate((res.mbids, chunk.mbids))
            res.startTimes = np.concatenate((res.startTimes, chunk.startTimes))
            res.durations = np.concatenate((res.durations, chunk.durations))
        return res

    # returns AnnotatedChromaSegments for the file list
    def loadChromasForAnnotationFileListFile(self, fileListFile):
        return self.loadChromasForAnnotationFileList(
            commonUtils.loadFileList(fileListFile))

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
            path.realpath(params.fileRef),
            params.chromaParameters.stepSize,
            params.chromaParameters.smoothingTime,
            params.chromaParameters.rollToCRoot,
            params.chromaParameters.sampleRate)

def extractAudioFileName(jsonFileName):
    with open(jsonFileName) as json_file:
        data = json.load(json_file)
        return str(path.realpath(data['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', commonUtils.getDataRoot())))

def smooth(x, window_len=11, window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """
    y = np.zeros(x.shape)
    for i in range(np.size(x,1)):
      if np.size(x, 0) < window_len:
          raise ValueError("Input vector needs to be bigger than window size.")
      if window_len < 3:
          return x
      if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
          raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")
      xx = x[:, i]
      s = np.r_[xx[window_len - 1:0:-1], xx, xx[-1:-window_len:-1]]
      # print(len(s))
      if window == 'flat':  # moving average
          w = np.ones(window_len, 'd')
      else:
          w = eval('np.' + window + '(window_len)')
      start = int(window_len / 2)
      end = start + len(xx)
      y[:,i] = np.convolve(w / w.sum(), s, mode='valid')[start:end]
    return y

@cacher.memory.cache
def rawChromaFromAudio(audiofile, sampleRate=44100, stepSize=2048):
    mywindow = np.array(
        [0.001769, 0.015848, 0.043608, 0.084265, 0.136670, 0.199341, 0.270509, 0.348162, 0.430105, 0.514023,
         0.597545, 0.678311, 0.754038, 0.822586, 0.882019, 0.930656, 0.967124, 0.990393, 0.999803, 0.999803,
         0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803,
         0.999803, 0.999803, 0.999803, 0.999803, 0.999803,
         0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999650, 0.996856, 0.991283,
         0.982963, 0.971942, 0.958281, 0.942058, 0.923362, 0.902299, 0.878986, 0.853553, 0.826144,
         0.796910, 0.766016, 0.733634, 0.699946, 0.665140, 0.629410, 0.592956, 0.555982, 0.518696,
         0.481304, 0.444018, 0.407044, 0.370590, 0.334860, 0.300054, 0.266366, 0.233984, 0.203090,
         0.173856, 0.146447, 0.121014, 0.097701, 0.076638, 0.057942, 0.041719, 0.028058, 0.017037,
         0.008717, 0.003144, 0.000350])
    audio = essentia.standard.MonoLoader(filename=audiofile, sampleRate=sampleRate)()
    # estimate audio duration just for caching purposes:
    audioDuration(audiofile, sampleRate=sampleRate, audioSamples=audio)

    stepsize, semitones = vamp.collect(
        audio, sampleRate, "nnls-chroma:nnls-chroma", output="semitonespectrum", step_size=stepSize)["matrix"]
    chroma = np.zeros((semitones.shape[0], 12))
    for i in range(semitones.shape[0]):
        tones = semitones[i] * mywindow
        cc = chroma[i]
        for j in range(tones.size):
            cc[j % 12] = cc[j % 12] + tones[j]
    # roll from 'A' based to 'C' based
    chroma = np.roll(chroma, shift=-3, axis=1)
    return chroma

def smoothedChromaFromAudio(audiofile, sampleRate=44100, stepSize=2048, smoothingTime=1.25):
    result = rawChromaFromAudio(audiofile, sampleRate, stepSize)
    return smooth(result, window_len=int(smoothingTime * sampleRate / stepSize), window='hanning').astype(
                         'float32')

@cacher.memory.cache(ignore=['cachedRawChroma'])
def loadAnnotatedNNLSChromas(
        jsonFileName,
        stepSize,
        smoothingTime,
        rollToCRoot,
        sampleRate,
        cachedRawChroma = None):
    audioFileName = extractAudioFileName(jsonFileName)
    if (cachedRawChroma is not None):
        chroma = cachedRawChroma
    else:
        chroma = rawChromaFromAudio(audioFileName, sampleRate, stepSize)
    chroma = smooth(
        chroma,
        window_len=int(smoothingTime * sampleRate / stepSize), window='hanning').astype('float32')
    with open(jsonFileName) as json_file:
        print(json_file)
        data = json.load(json_file)
        mbid = data['mbid']
        duration = data['duration']
        metreNumerator = int(data['metre'].split('/')[0])
        allBeats = []
        allChords = []
        commonUtils.processParts(metreNumerator, data, allBeats, allChords, 'chords')
        segments = commonUtils.toBeatChordSegments(0, duration, allBeats, allChords)
        #
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
                print("empty segment ", segments[i].startTime, segments[i].endTime)
                raise
            chromas[i] = chroma[s]
            if (rollToCRoot):
                shift = 12 - pitch
                chromas[i] = np.roll(chromas[i], shift=shift)
            labels[i] = segments[i].symbol
            kinds[i] = kind
            mbids[i] = mbid
            startTimes[i] = segments[i].startTime
            durations[i] = float(segments[i].endTime) - float(segments[i].startTime)
        return AnnotatedChromaSegments(labels, kinds, chromas, mbids, startTimes, durations)

@cacher.memory.cache(ignore=['cachedRawChroma'])
def loadNNLSChromas(
        audioInputFile,
        stepSize,
        smoothingTime,
        sampleRate,
        startTimes,
        durations,
        cachedRawChroma = None):
    if (cachedRawChroma is not None):
        chroma = cachedRawChroma
    else:
        chroma = rawChromaFromAudio(audioInputFile, sampleRate, stepSize)
    # TODO: make possible averaging by interbeat intervals.
    chroma = smooth(
        chroma,
        window_len=int(smoothingTime * sampleRate / stepSize), window='hanning').astype('float32')
    # Only take beat-centered chromas
    indices = map(lambda x: int(float(x) *
                sampleRate / stepSize), startTimes)
    return ChromaSegments(chroma[indices], startTimes, durations)

@cacher.memory.cache(ignore=['sampleRate', 'audioSamples'])
def audioDuration(audioFileName, sampleRate=44100, audioSamples=None):
    if (audioSamples is not None):
        return float(len(audioSamples)) / sampleRate
    else:
        audio = essentia.standard.MonoLoader(filename=audioFileName, sampleRate=sampleRate)()
        return float(len(audio)) / sampleRate

@cacher.memory.cache
def rnnBeatSegments(audioFileName):
    proc = mf.BeatTrackingProcessor(
        fps = 100,
        method='comb', min_bpm=40,
        max_bpm=240, act_smooth=0.09,
        hist_smooth=7, alpha=0.79)
    act = mf.RNNBeatProcessor()(str(audioFileName))
    stamps = proc(act).astype('float32')
    # the last beat is lost, but who cares...
    # TODO: fix this approach
    startTimes = np.array(stamps[0:-1])
    durations = np.array(map(lambda x: stamps[x+1] - stamps[x], xrange(len(startTimes))))
    # filter out algorithm artefacts
    startTimes = startTimes[durations > 0.05]
    durations = durations[durations > 0.05]
    return BeatSegments(startTimes, durations)
