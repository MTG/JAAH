import sys
import json
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
        res.append(ChordSegment(onsets[i], onsets[i+1], sym))
    if (res[-1].endTime < endTime) :
        res.append(ChordSegment(res[-1].endTime, endTime, 'N'))
    return mergeSegments(res)


def processChords(blocks, allChords):
    for block in blocks:
        bars = block.split('|')[1:-1]
        for bar in bars:
            chords = [c for c in re.split('\s+', bar) if c != '']
            if len(chords) == 1 :
                chords = chords * 4
            elif len(chords) == 2 :
                chords = [chords[0], chords[0], chords[1], chords[1]]
            elif len(chords) != 4:
                raise ValueError("Wrong number of chords in a bar: " + bar)
            allChords.extend(chords)

def processParts(data, beats, chords):
    if ('parts' in data.keys()):
        for part in data['parts']:
            processParts(part, beats, chords)
    else:
        beats.extend(data['beats'])
        processChords(data['chords'], chords)

try:
    infile = sys.argv[1]
    outfile = sys.argv[2]
except:
    print "usage:", sys.argv[0], "<input json file> <output lab file>"
    sys.exit()

with open(infile, 'r') as data_file:
    data = json.load(data_file)
    duration = data['duration']
    metre = data['metre']
    if (metre != '4/4') :
        raise ValueError("Only 4/4 metre is supported so far.")
    allBeats = []
    allChords = []
    processParts(data, allBeats, allChords)
    segments = toMirexLab(0, duration, allBeats, allChords)
    with open(outfile, 'w') as content_file:
        for s in segments:
            content_file.write(str(s) + '\n')
