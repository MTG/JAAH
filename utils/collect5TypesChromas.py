import os
import sys
from chordUtils import json2lab
from subprocess import call
import json
import argparse
import chordUtils
import essentia.standard
import vamp
import numpy as np
import re

sampleRate = 44100

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

def chromaFromAudio(audiofile, stepSize=2048):
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
    return smooth(chroma, window_len= int(2.75 * sampleRate / stepSize), window='hanning').astype('float32')

pitches = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'B':11}
alt={'b':-1, '#':1}
shortcuts={'maj':'(3,5)', 'min':'(b3,5)', 'dim':'(b3,b5)', 'aug':'(3,#5)', 'maj7':'(3,5,7)',
'min7':'(b3,5,b7)', '7':'(3,5,b7)', 'dim7':'(b3,b5,bb7)', 'hdim7':'(b3,b5,b7)',
'minmaj7':'(b3,5,7)', 'maj6':'(3,5,6)', 'min6':'(b3,5,6)', '9':'(3,5,b7,9)',
'maj9':'(3,5,7,9)', 'min9':'(b3,5,b7,9)', 'sus4':'(4,5)'}

def toPitchAndKind(label):
    parts = label.split(':')
    note = parts[0].split('/')[0]
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
    if ('3' in degrees and 'b7' in degrees):
        kind='dom'
    elif ('3' in degrees and '5' in degrees):
        kind='maj'
    elif ('b3' in degrees):
        if ('b5' in degrees and 'b7' in degrees):
            kind='hdim7'
        elif ('b5' in degrees and 'bb7' in degrees):
            kind = 'dim7'
        elif ('5' in degrees):
            kind = 'min'
        else:
            kind='unclassified'
    else:
        kind = 'unclassified'
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
        segments = chordUtils.toMirexLab(0, duration, allBeats, allChords)
        #
        stepSize = 2048
        chroma = chromaFromAudio(audiofile, stepSize=stepSize)
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
            # roll ->  C (and from 'A' based to 'C' based)
            shift = pitch - 3
            if (shift < 0) :
                shift = 12 + shift
            chromas[i]= np.roll(np.median(chroma[s:e], axis=0), shift=shift, axis=0)
            labels[i] = segments[i].symbol
            kinds[i] = kind
            mbids[i]=mbid
            start_times[i]=segments[i].startTime
            durations[i] = float(segments[i].endTime) - float(segments[i].startTime)
        return chromas, labels, kinds, mbids, start_times, durations

utils_path = os.path.dirname(os.path.realpath(__file__))
eval_dir = "evaluation"
data_root = os.environ['JAZZ_HARMONY_DATA_ROOT']
if not os.path.exists(eval_dir):
    os.mkdir(eval_dir)

parser = argparse.ArgumentParser(
    description='Collect chroma statistics on given dataset'
                ' (distribution by 5 basic chord types: maj, min, dom, dim7, hdim7 + unclassified')

parser.add_argument('infile', type=argparse.FileType('r'), help='npz input file')
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
# BUGS: NaNs in chroma matrix.
