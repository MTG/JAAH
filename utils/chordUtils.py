import json
import re
import numpy as np

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

def toMirexLab(startTime, endTime, onsets, symbols) :
    if (len(onsets) < len(symbols)) :
        raise ValueError("inappropriate lists lengths")
    if (len(onsets) == len(symbols)) :
        onsets = onsets + [endTime]
    res = []
    if (startTime < onsets[0]) :
        res.append(ChordSegment(startTime, onsets[0], 'N'))
    for i in xrange(len(symbols)) :
        sym = symbols[i]
        if (onsets[i] < onsets[i+1]):
            res.append(ChordSegment(onsets[i], onsets[i+1], sym))
        else:
            raise ValueError("wrong beats order: " + str(onsets[i]) + ", " + str(onsets[i+1]))
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
        segments = mergeSegments(toMirexLab(0, duration, allBeats, allChords))
        with open(outfile, 'w') as content_file:
            for s in segments:
                content_file.write(str(s) + '\n')

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


