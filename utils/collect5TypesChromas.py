import os
import sys
from chordUtils import json2lab
from subprocess import call
import json
import argparse
import chordUtils
import numpy as np
import re

sampleRate = 44100

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

def process(infile) :
    with open(infile) as json_file:
        print json_file
        data = json.load(json_file)
        mbid = data['mbid']
        audiofile = data['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', data_root)
        duration = data['duration']
        metreNumerator = int(data['metre'].split('/')[0])
        allBeats = []
        allChords = []
        chordUtils.processParts(metreNumerator, data, allBeats, allChords, 'chords')
        segments = chordUtils.toBeatChordSegments(0, duration, allBeats, allChords)
        #
        stepSize = 2048
        chroma, l = chordUtils.chromaFromAudio(audiofile, sampleRate=sampleRate, stepSize=stepSize)
        chromas = np.zeros((len(segments), 12), dtype='float32')
        labels = np.empty(len(segments), dtype='object')
        kinds = np.empty(len(segments), dtype='object')
        mbids = np.empty(len(segments), dtype='object')
        start_times = np.zeros(len(segments), dtype='float32')
        durations = np.zeros(len(segments), dtype='float32')
        for i in range(len(segments)):
            pitch, kind = toPitchAndKind(segments[i].symbol)
            s = int(float(segments[i].startTime) * sampleRate / stepSize)
            e = int(float(segments[i].endTime) * sampleRate / stepSize)
            if (s == e):
                print "empty segment ", segments[i].startTime, segments[i].endTime
                raise
            # print s, e
            # print segments[i].startTime, segments[i].endTime
            # roll ->  C (and from 'A' based to 'C' based)
            shift = -3 - pitch
            if (shift < 0) :
                shift = 12 + shift
            # np.median is quite questionable. ? just sample for s? or for every beat from s to e?
            # chromas[i]= np.roll(np.median(chroma[s:e], axis=0), shift=shift, axis=0)
            chromas[i]= np.roll(chroma[s], shift=shift, axis=0)
            labels[i] = segments[i].symbol
            kinds[i] = kind
            mbids[i]=mbid
            start_times[i]=segments[i].startTime
            durations[i] = float(segments[i].endTime) - float(segments[i].startTime)
        return chromas, labels, kinds, mbids, start_times, durations

eval_dir = "evaluation"
data_root = os.environ['JAZZ_HARMONY_DATA_ROOT']
if not os.path.exists(eval_dir):
    os.mkdir(eval_dir)

parser = argparse.ArgumentParser(
    description='Collect chroma statistics on given dataset'
                ' (distribution by 5 basic chord types: maj, min, dom, dim, hdim7 + unclassified')

parser.add_argument('infile', type=argparse.FileType('r'), help='txt input file (with list of json annotations)')
parser.add_argument('--output', '-o', type=argparse.FileType('w'), default='out.npz', help='output .npz file')

args = parser.parse_args()

infile = args.infile.name
chromas=np.zeros((0,12), dtype='float32')
labels=np.array([], dtype='object')
kinds=np.array([], dtype='object')
mbids=np.array([], dtype='object')
start_times=np.array([], dtype='float32')
durations=np.array([], dtype='float32')
with open(infile) as list_file:
    for line in list_file:
        next_chromas, next_labels, next_kinds, next_mbids, next_start_times, next_durations = process(line.rstrip())
        chromas=np.concatenate((chromas, next_chromas))
        labels=np.concatenate((labels, next_labels))
        kinds=np.concatenate((kinds, next_kinds))
        mbids=np.concatenate((mbids, next_mbids))
        start_times=np.concatenate((start_times, next_start_times))
        durations=np.concatenate((durations, next_durations))
chordUtils.saveDatasetChroma(
    args.output.name,
    chromas=chromas,
    labels=labels,
    kinds=kinds,
    mbids=mbids,
    start_times=start_times,
    durations=durations)
print 'output is written to ', args.output.name
# TODO: visualization of single chroma and disttribution
