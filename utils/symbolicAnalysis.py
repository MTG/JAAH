import cacher
import json
import commonUtils
import numpy as np
import lowLevelFeatures as ll
from collections import Counter
from collections import OrderedDict
import chordModel
import os

class SymbolicAnalysisSegment :
    def __init__(self, labels, kind, root, duration, nBeats):
        self.labels = labels
        self.kind = kind
        self.root = root
        self.duration = duration
        self.nBeats = nBeats
    def __repr__(self):
        return str(self.labels) + '\t' + self.kind + '\t' + str(self.duration) + '\t' + self.nBeats

def toSymbolicAnalysisSegments(chordSegments) :
    result = np.empty([len(chordSegments)], dtype='object')
    i = 0
    for segment in chordSegments:
        pitch, kind = ll.toPitchAndKind(segment.symbol)
        duration = float(segment.endTime) - float(segment.startTime)
        result[i] = SymbolicAnalysisSegment(set([segment.symbol]), kind, pitch, duration, 1)
        i += 1
    return result

def merge(symbolicAnalysisSegments) :
    if (len(symbolicAnalysisSegments) < 2) :
        return symbolicAnalysisSegments
    res = []
    currentSegment = symbolicAnalysisSegments[0]
    for segment in symbolicAnalysisSegments[1:] :
        if (segment.kind == currentSegment.kind and segment.root == currentSegment.root):
            currentSegment.duration += segment.duration
            currentSegment.nBeats += segment.nBeats
        else:
            res.append(currentSegment)
            currentSegment = segment
    res.append(currentSegment)
    return res

INTERTVALS = ['P1', 'm2', 'M2', 'm3', 'M3', 'P4', 'd5', 'P5', 'm6', 'M6', 'm7', 'M7']

def toInterval(pitch1, pitch2) :
    return INTERTVALS[(pitch2 - pitch1) % 12]

def toSequence(intervals) :
    return reduce(lambda x,y: x + "-" + y.split('-',1)[1], intervals)

def updateNGrams(segments, twoGrams, nGrams, limit):
    # ignore unclassified.
    kinds = map(lambda x: x.kind, filter(lambda x: x.kind != ll.UNCLASSIFIED, segments))
    roots = map(lambda x: x.root, filter(lambda x: x.kind != ll.UNCLASSIFIED, segments))
    sequence = np.empty([len(kinds) - 1], dtype='object')
    for i in xrange(len(sequence)):
        sequence[i] = kinds[i] + '-' + toInterval(roots[i], roots[i + 1]) + '-' + kinds[i + 1]
    for s in sequence:
        twoGrams[s] += 1
    for i in xrange(len(sequence)):
        if (i == 0):
            nGrams[sequence[i]] +=1
        for j in (xrange(i,max(0, i - limit),-1)):
            nGrams[toSequence(sequence[j:i + 1])] += 1

def makeTransitionCRootPart(twoGrams, harmonicRhythm):
    result = np.zeros((chordModel.N_CHORDS, chordModel.N_CHORD_KINDS))
    for i in xrange(chordModel.N_CHORD_KINDS):
        column = result[:, i]
        sym = chordModel.CHORD_KINDS[i]
        relatedKeys = filter(lambda x: x.endswith(sym), twoGrams.keys())
        denominator = float(sum([twoGrams[x] for x in relatedKeys])) * harmonicRhythm
        # probability for unobserved (i.e. near impossible) events
        if (denominator == 0):
            # chord is not used.
            denominator = chordModel.N_CHORDS * harmonicRhythm
        pUnobserved = 1.0 / denominator
        for key in relatedKeys:
            chord, interval, dummy = key.split('-')
            # inverse interval, since we trace it backwrds
            nInterval = -INTERTVALS.index(interval) % 12
            nChord = chordModel.CHORD_KINDS.index(chord)
            pos = chordModel.N_CHORD_KINDS * nInterval + nChord
            column[pos] = float(twoGrams[key]) / denominator
        # imply harmonic rhythm (chord inertia).
        column[i] = 1.0 - 1.0/harmonicRhythm
        column[column == 0] = pUnobserved
        column /= sum(column)
    return result

def harmonicRhythmForFile(annoFileName):
   with open(annoFileName) as json_file:
       data = json.load(json_file)
       duration = data['duration']
       metreNumerator = int(data['metre'].split('/')[0])
       allBeats = []
       allChords = []
       commonUtils.processParts(metreNumerator, data, allBeats, allChords, 'chords')
       segments = merge(toSymbolicAnalysisSegments(
           commonUtils.toBeatChordSegments(0, duration, allBeats, allChords)))
        # remove unclassified.
       nBeats = map(lambda x: x.nBeats, filter(lambda x: x.kind!= ll.UNCLASSIFIED, segments))
       return float(sum(nBeats)) / len(nBeats)

def harmonicRhythmForEachFileInList(fileList):
    resultByFile = {}
    with open(fileList) as list_file:
        for line in list_file:
            infile = line.rstrip()
            basename = os.path.basename(infile)
            name, jsonExt = os.path.splitext(basename)
            resultByFile[name] = harmonicRhythmForFile(infile)
    return resultByFile

class ChordUsageSummary:
    def __init__(self, beatsNumber, beatsPercent, durationSeconds, durationPercent):
        self.beatsNumber = beatsNumber
        self.beatsPercent = beatsPercent
        self.durationSeconds = durationSeconds
        self.durationPercent = durationPercent

class SymbolicStatistics :
    def __init__(self, totalDurations, totalBeats, labelKinds, noBassKinds, chordSummaryDict, unclassifiedLabelsCounter, meanHarmonicRhythm, meanBPM,
                 numberOfSegments, numberOfDistinctNGrams, maxNGramLengthWithinTop):
        self.totalDurations = totalDurations
        self.totalBeats = totalBeats
        self.labelKinds = labelKinds
        self.noBassKinds = noBassKinds
        self.chordSummaryDict = chordSummaryDict
        self.unclassifiedLabelsCounter = unclassifiedLabelsCounter
        self.meanHarmonicRhythm = meanHarmonicRhythm
        self.meanBPM = meanBPM
        self.numberOfSegments = numberOfSegments
        self.numberOfDistinctNGrams = numberOfDistinctNGrams
        self.maxNGramLengthWithinTop = maxNGramLengthWithinTop

@cacher.memory.cache
def estimateStatistics(fileList, top = 300, maxNGram = 2000):
    allLabels = np.array([], dtype='object')
    allKinds = np.array([], dtype='object')
    allRoots = np.array([], dtype='object')
    allDurations = np.array([], dtype='float32')
    allNBeats = np.array([], dtype='int')
    twoGrams = Counter()
    nGrams = Counter()
    nFiles = 0
    for infile in fileList:
        nFiles += 1
        print infile
        with open(infile) as json_file:
            data = json.load(json_file)
            duration = data['duration']
            metreNumerator = int(data['metre'].split('/')[0])
            allBeats = []
            allChords = []
            commonUtils.processParts(metreNumerator, data, allBeats, allChords, 'chords')
            segments = merge(toSymbolicAnalysisSegments(
                commonUtils.toBeatChordSegments(0, duration, allBeats, allChords)))
            updateNGrams(segments, twoGrams, nGrams, limit = maxNGram)
            allLabels = np.append(allLabels, map(lambda x: x.labels, segments))
            allKinds = np.append(allKinds, map(lambda x: x.kind, segments))
            allRoots = np.append(allRoots, map(lambda x: x.root, segments))
            allDurations = np.append(allDurations, map(lambda x: x.duration, segments))
            allNBeats = np.append(allNBeats, map(lambda x: x.nBeats, segments))

    # output: kinds
    totalDuration = sum(allDurations)
    totalBeats = sum(allNBeats)
    labelKinds = Counter()
    noBasslabelKinds = Counter()

    for labelSet in allLabels:
        for l in labelSet:
            parts = l.split(':')
            if (len(parts) == 1):
                labelKinds['maj'] += 1
                noBasslabelKinds['maj'] += 1
            else:
                labelKinds[parts[1]] += 1
                noBasslabelKinds[parts[1].split('/')[0]] += 1
    print infile, totalDuration
    majDuration = sum(allDurations[allKinds == 'maj'])
    minDuration = sum(allDurations[allKinds == 'min'])
    domDuration = sum(allDurations[allKinds == 'dom'])
    hdimDuration = sum(allDurations[allKinds == 'hdim7'])
    dimDuration = sum(allDurations[allKinds == 'dim'])
    ncDuration = sum(allDurations[allLabels == set('N')])
    unclassifiedDuration = sum(allDurations[allKinds == ll.UNCLASSIFIED]) - ncDuration
    majBeats = sum(allNBeats[allKinds == 'maj'])
    minBeats = sum(allNBeats[allKinds == 'min'])
    domBeats = sum(allNBeats[allKinds == 'dom'])
    hdimBeats = sum(allNBeats[allKinds == 'hdim7'])
    dimBeats = sum(allNBeats[allKinds == 'dim'])
    ncBeats = sum(allNBeats[allLabels == set('N')])
    unclassifiedBeats = sum(allNBeats[allKinds == ll.UNCLASSIFIED]) - ncBeats

    chordSummaryDict = OrderedDict()
    chordSummaryDict['maj'] = ChordUsageSummary(
        majBeats,  majBeats * 100.0 / totalBeats, majDuration,  majDuration * 100.0 / totalDuration)
    chordSummaryDict['min'] = ChordUsageSummary(
        minBeats,  minBeats * 100.0 / totalBeats, minDuration,  minDuration * 100.0 / totalDuration)
    chordSummaryDict['dom'] = ChordUsageSummary(
        domBeats,  domBeats * 100.0 / totalBeats, domDuration,  domDuration * 100.0 / totalDuration)
    chordSummaryDict['hdim7'] = ChordUsageSummary(
        hdimBeats,  hdimBeats * 100.0 / totalBeats, hdimDuration,  hdimDuration * 100.0 / totalDuration)
    chordSummaryDict['dim'] = ChordUsageSummary(
        dimBeats,  dimBeats * 100.0 / totalBeats, dimDuration,  dimDuration * 100.0 / totalDuration)
    chordSummaryDict['N'] = ChordUsageSummary(
        ncBeats,  ncBeats * 100.0 / totalBeats, ncDuration,  ncDuration * 100.0 / totalDuration)
    chordSummaryDict['unclassified'] = ChordUsageSummary(
        unclassifiedBeats,  unclassifiedBeats * 100.0 / totalBeats, unclassifiedDuration,  unclassifiedDuration * 100.0 / totalDuration)
    # what's unclassified
    unclassified = np.array([], dtype='object')
    for u in allLabels[allKinds == ll.UNCLASSIFIED]:
        unclassified = np.append(unclassified, list(u))

    # remove unclassified.
    labels = allLabels[allKinds != ll.UNCLASSIFIED]
    kinds = allKinds[allKinds != ll.UNCLASSIFIED]
    roots = allRoots[allKinds != ll.UNCLASSIFIED]
    durations = allDurations[allKinds != ll.UNCLASSIFIED]
    nBeats = allNBeats[allKinds != ll.UNCLASSIFIED]

    harmonicRhythm = float(sum(nBeats)) / len(nBeats)
    transitionCRootPart = makeTransitionCRootPart(twoGrams, harmonicRhythm)
    transitionMatrix = transitionCRootPart
    for i in xrange(1, chordModel.N_PITCH_CLASSES):
        block = np.roll(transitionCRootPart, i * chordModel.N_CHORD_KINDS, 0)
        transitionMatrix = np.hstack((transitionMatrix, block))

    topTwoGrams = twoGrams.most_common(top)
    topNGrams = nGrams.most_common(top)
    maxTopLen = max([x[0].count('-')/2 for x in topNGrams])
    symStat = SymbolicStatistics(
        totalDuration,
        totalBeats,
        labelKinds,
        noBasslabelKinds,
        chordSummaryDict,
        Counter(unclassified),
        harmonicRhythm,
        60.0 / (totalDuration / totalBeats),
        len(kinds),
        len(nGrams),
        maxTopLen)

    return symStat, topTwoGrams, topNGrams, transitionMatrix

def saveTransitionMatrix(outfile, matrix):
    np.savez(
        outfile,
        matrix=matrix)

def loadTransitionMatrix(infile):
    data = np.load(infile)
    return data['matrix']

######################################################################

#parser = argparse.ArgumentParser(
#    description='Evaluate chord prediction accuracy on given file list')
#
#parser.add_argument('infile', type=argparse.FileType('r'), help='txt input file (with list of json annotations)')
#
#args = parser.parse_args()
#
#listFile = args.infile.name
#symStat, topTwoGrams, topNGrams, transitionMatrix = estimateStatistics(commonUtils.loadFileList(listFile), 10, 10)