import json
import os
import numpy as np
import essentia.standard
import vamp
from madmom.features.beats import BeatTrackingProcessor
from madmom.features.beats import RNNBeatProcessor
from sklearn.externals import joblib
from sklearn.model_selection import KFold
from sklearn import preprocessing
from subprocess import call
import re

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

def toMirexLab(startTime, endTime, onsets, symbols, strengths) :
    if (len(onsets) < len(symbols) or len(symbols) != len(strengths)) :
        raise ValueError("inappropriate lists lengths")
    if (len(onsets) == len(symbols)) :
        onsets = np.concatenate((onsets, [endTime]))
    res = []
    if (startTime < onsets[0]) :
        res.append(ChordSegment(startTime, onsets[0], 'N'))
    for i in xrange(len(symbols)) :
        sym = symbols[i] if strengths[i] > 0 else 'N'
        res.append(ChordSegment(onsets[i], onsets[i+1], sym))
    if (res[-1].endTime < endTime) :
        res.append(ChordSegment(res[-1].endTime, endTime, 'N'))
    return mergeSegments(res)

def toBeatChordSegments(startTime, endTime, beats, symbols) :
    if (len(beats) < len(symbols)) :
        raise ValueError("inappropriate lists lengths")
    if (len(beats) == len(symbols)) :
        beats = beats + [endTime]
    res = []
    if (startTime < beats[0]) :
        res.append(ChordSegment(startTime, beats[0], 'N'))
    for i in xrange(len(symbols)) :
        sym = symbols[i]
        if (beats[i] < beats[i+1]):
            res.append(ChordSegment(beats[i], beats[i + 1], sym))
        else:
            print "wrong beats order: " + str(beats[i]) + ", " + str(beats[i + 1])
        #    raise ValueError("wrong beats order: " + str(onsets[i]) + ", " + str(onsets[i+1]))
    if (res[-1].endTime < endTime) :
        res.append(ChordSegment(res[-1].endTime, endTime, 'N'))
    return res

def allDivisors(n, startWith = 1):
    i = startWith
    if n < i:
        return set()
    if n % i == 0:
        return set((i, n / i)) |  allDivisors(n / i, i + 1)
    else:
        return allDivisors(n, i + 1)

def processChords(numerator, blocks, allChords):
    for block in blocks:
        bars = block.split('|')[1:-1]
        for bar in bars:
            chords = [c for c in re.split('\s+', bar) if c != '']
            divisors = allDivisors(numerator)
            if not (len(chords) in divisors):
                raise ValueError("Wrong number of chords in a bar: " + bar)
            multiplier = numerator / len(chords)
            newchords = []
            for c in chords:
                newchords.extend([c] * multiplier)
            allChords.extend(newchords)

def processParts(metreNumerator, data, beats, chords, choice):
    if ('parts' in data.keys()):
        for part in data['parts']:
            processParts(metreNumerator, part, beats, chords, choice)
    else:
        if 'metre' in data :
            metreNumerator = int(data['metre'].split('/')[0])
        beats.extend(data['beats'])
        processChords(metreNumerator, data[choice], chords)

def json2lab(choice, infile, outfile):
    with open(infile, 'r') as data_file:
        data = json.load(data_file)
        duration = data['duration']
        metreNumerator = int(data['metre'].split('/')[0])
        allBeats = []
        allChords = []
        processParts(metreNumerator, data, allBeats, allChords, choice)
        segments = mergeSegments(toBeatChordSegments(0, duration, allBeats, allChords))
        with open(outfile, 'w') as content_file:
            for s in segments:
                content_file.write(str(s) + '\n')

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
          raise ValueError, "Input vector needs to be bigger than window size."
      if window_len < 3:
          return x
      if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
          raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
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

def chromaFromAudio(audiofile, sampleRate=44100, stepSize=2048, smoothingTime=1.3):
    mywindow = np.array([0.001769, 0.015848, 0.043608, 0.084265, 0.136670, 0.199341, 0.270509, 0.348162, 0.430105, 0.514023,
                0.597545, 0.678311, 0.754038, 0.822586, 0.882019, 0.930656, 0.967124, 0.990393, 0.999803, 0.999803,
                0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803,
                0.999803, 0.999803, 0.999803,  0.999803, 0.999803,
                0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999803, 0.999650, 0.996856, 0.991283,
                      0.982963, 0.971942, 0.958281, 0.942058, 0.923362, 0.902299, 0.878986, 0.853553, 0.826144,
                      0.796910, 0.766016, 0.733634, 0.699946, 0.665140, 0.629410, 0.592956, 0.555982, 0.518696,
                      0.481304, 0.444018, 0.407044, 0.370590, 0.334860, 0.300054, 0.266366, 0.233984, 0.203090,
                      0.173856, 0.146447, 0.121014, 0.097701, 0.076638, 0.057942, 0.041719, 0.028058, 0.017037,
                      0.008717, 0.003144, 0.000350])
    audio = essentia.standard.MonoLoader(filename=audiofile, sampleRate=sampleRate)()
    parameters = {}
    stepsize, semitones = vamp.collect(
        audio, sampleRate, "nnls-chroma:nnls-chroma", output="semitonespectrum", step_size=stepSize)["matrix"]
    chroma = np.zeros((semitones.shape[0], 12))
    for i in range(semitones.shape[0]):
        tones = semitones[i] * mywindow
        cc = chroma[i]
        for j in range(tones.size):
            cc[j % 12] = cc[j % 12] + tones[j]
    return smooth(chroma, window_len= int(smoothingTime * sampleRate / stepSize), window='hanning').astype('float32'), len(audio)

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

def calculateBeatsAndChroma(infile, stepSize=2048, smoothingTime=1.3):
    print 'Loading audio file...', infile
    proc = BeatTrackingProcessor(
        fps = 100,
        method='comb', min_bpm=40,
        max_bpm=240, act_smooth=0.09,
        hist_smooth=7, alpha=0.79)
    act = RNNBeatProcessor()(infile)
    beats = proc(act).astype('float32')

    chroma, l = chromaFromAudio(infile, stepSize=stepSize, smoothingTime=smoothingTime)
    return l, beats, chroma

# returns len(beats)x60 array
def chordLogProbabilities(amodel, hopSize, sampleRate, chroma, beats):
    probs = np.zeros((len(beats) - 1, 60))
    indices = map(lambda x: int(float(sampleRate) * beats[x] / hopSize), xrange(len(beats) - 1))
    amaj=amodel[0]
    amin=amodel[1]
    adom=amodel[2]
    ahdim7=amodel[3]
    adim=amodel[4]
    decimatedChroma = chroma[indices]
    for basePitch in range(12):
        pos = basePitch * 5
        # TODO: class
        #probs[:, pos] = amaj.score_samples(decimatedChroma)
        #probs[:, pos + 1] = amin.score_samples(decimatedChroma)
        #probs[:, pos + 2] = adom.score_samples(decimatedChroma)
        #probs[:, pos + 3] = ahdim7.score_samples(decimatedChroma)
        #probs[:, pos + 4] = adim.score_samples(decimatedChroma)
        d11Chroma = normalizeTo11d(decimatedChroma)
        probs[:, pos] = amaj.score_samples(d11Chroma)
        probs[:, pos + 1] = amin.score_samples(d11Chroma)
        probs[:, pos + 2] = adom.score_samples(d11Chroma)
        probs[:, pos + 3] = ahdim7.score_samples(d11Chroma)
        probs[:, pos + 4] = adim.score_samples(d11Chroma)
        decimatedChroma = np.roll(decimatedChroma, -1, axis=1)
    return  probs

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
    s = np.log(trellis[0,:])
    for i in xrange(1, trellis.shape[0]):
        s, prev = viterbiStep(s, logMatrix)
        paths[i, :] = prev
        s = s + np.log(trellis[i,:])
    best = np.empty(trellis.shape[0], dtype='int')
    p = np.argmax(s)
    for i in xrange(trellis.shape[0] - 1, -1, -1):
        best[i] = p
        p = paths[i, p]
    return best


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


def callChordino(chordino_dir, chordino_ext, audioInFile, name):
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

def callJazz(jazz_dir, jazz_ext, audioInFile, name):
    # chordino
    if not os.path.exists(jazz_dir):
        os.mkdir(jazz_dir)
    oursFile = os.path.join(jazz_dir, name + "." + jazz_ext)
    # TODO: class
    chordBeats(audioInFile, oursFile, smoothingTime=2.75)
    return oursFile

def callMusOOEvaluatorForSingleFile(dir, name, ext, chords, testFile, refFile):
    chordsFile = os.path.join(dir, name + "." + ext + "." + chords + ".txt")
    print testFile
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
    segmentationFile = os.path.join(testdir, "accuracy." + ".segmentation.txt")
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

def evaluateFileList(
        jsonList,
        eval_dir = "tmp_chordino_evaluation",
        truth_dir = "tmp_true_chords",
        nameListFile="tmp_names.txt",
        predictionFun = callChordino):
    data_root = os.environ['JAZZ_HARMONY_DATA_ROOT']
    if not os.path.exists(eval_dir):
        os.mkdir(eval_dir)
    if not os.path.exists(truth_dir):
        os.mkdir(truth_dir)
    nf = open(nameListFile, "w")
    with open(jsonList) as list_file:
        for line in list_file:
            infile = line.rstrip()
            basename = os.path.basename(infile)
            name, ext = os.path.splitext(basename)
            nf.write(name + "\n")
            labfile = os.path.join(truth_dir, name + ".lab")
            json2lab('chords', infile, labfile)
            with open(infile) as json_file:
                data = json.load(json_file)
                audiofile = data['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', data_root)
                predictionFun(eval_dir, "lab", audiofile, name)
    nf.close()
    chordsFile, segmentationFile = callMusOOEvaluatorForFileList(
        nameListFile,
        truth_dir,
        eval_dir)
    return extractMusOOAverageScore(chordsFile)

def extractMusOOAverageScore(scoreFile) :
    with open(scoreFile, 'r') as content_file:
        content = content_file.read()
        s = re.search("Average score: ([^%]*)%", content)
        return float(s.group(1))

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
    l, beats, chroma = calculateBeatsAndChroma(str(infile), smoothingTime=smoothingTime)
    # TODO: class
    #chroma = normalizeTo11d(chroma)
    noteNames = ["A", "Bb", "B", "C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab"]
    chordNames = np.empty(60, dtype='object')
    for i in xrange(12):
        p = i * 5
        chordNames[p] = noteNames[i]
        chordNames[p + 1] = noteNames[i] + ":min"
        chordNames[p + 2] = noteNames[i] + ":7"
        chordNames[p + 3] = noteNames[i] + ":hdim7"
        chordNames[p + 4] = noteNames[i] + ":dim"
    probs = chordLogProbabilities(amodel, 2048, 44100, chroma, beats)

    # No HMM so far...
    indices = np.argmax(probs, axis=1)
    syms = map(lambda x: chordNames[x], indices)
    s = probs[xrange(len(indices)), indices]
    strengths = np.exp(s)
    strengths[s == 0] = 0
    segments = toMirexLab(0.0, l / 44100.0, beats, syms, strengths)
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



