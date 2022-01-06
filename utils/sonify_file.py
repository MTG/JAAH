import os
from subprocess import call
import json
import argparse
import numpy as np
import essentia.standard as ess
from pychord_tools.common_utils import process_parts, to_beat_chord_segment_list, merge_segments
from pychord_tools.labels import PITCH_CLASS_NAMES, SHORTCUTS, note_to_number

import json
import re

DEGREE_TO_SEMITONES = {
    '1':0, '2':2, '3':4, '4':5, '5':7, '6':9, '7': 11, '9':14, '11':17, '13':21
}


def symbol_to_frequencies(symbol):
    parts_and_bass = symbol.split('/')
    parts = parts_and_bass[0].split(':')
    note = parts[0]
    if note[0] == 'N':
        return []

    pitch = note_to_number(note)
    midi = 60 + pitch

    if len(parts) == 1:
        kind = 'maj'
    else:
        kind = parts[1].split('/')[0]
    if kind in SHORTCUTS:
        kind = SHORTCUTS[kind]
    degrees = set(re.sub("[\(\)]", "", kind).split(','))
    if '3' in degrees and 'b7' in degrees:
        # frop fifth from dominant seventh
        degrees.remove('5')
    degrees.add('1')
    frequencies = []
    for d in degrees:
        semitones = DEGREE_TO_SEMITONES[d[-1]]
        if d[0] == '#':
            semitones += 1
        elif d[0] == 'b':
            semitones -= 1
        frequencies.append(f_pitch(midi + semitones))
    return frequencies


def generate_shepard_tone(freqs, dur=0.5, Fs=44100, amp=1):
    """Generate Shepard tones

    Based on:
    https://www.audiolabs-erlangen.de/resources/MIR/FMP/C1/C1S1_ChromaShepard.html

    Args:
        freq (float): Frequency of Shepard tone (Default value = 440)
        dur (float): Duration (in seconds) (Default value = 0.5)
        Fs (scalar): Sampling rate (Default value = 44100)
        amp (float): Amplitude of generated signal (Default value = 1)

    Returns:
        x (np.ndarray): Shepard tone
        t (np.ndarray): Time axis (in seconds)
    """
    N = int(dur * Fs)
    t = np.arange(N) / Fs
    num_sin = 1
    res = np.zeros(N)
    for freq in freqs:
        x = np.sin(2 * np.pi * freq * t)
        freq_lower = freq / 2
        while freq_lower > 20:
            num_sin += 1
            x = x + np.sin(2 * np.pi * freq_lower * t)
            freq_lower = freq_lower / 2
        freq_upper = freq * 2
        while freq_upper < 20000:
            num_sin += 1
            x = x + np.sin(2 * np.pi * freq_upper * t)
            freq_upper = freq_upper * 2
        x = x / num_sin
        x = (amp/float(len(freqs))) * x / np.max(x)
        res = res + x
    return res

def f_pitch(p):
    F_C4 = 261.63
    return F_C4 * 2 ** ((p - 60) / 12)


utils_path = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Sonify chord annotations with Shepard tones.')

parser.add_argument(
    '-i', '--input', type=argparse.FileType('r'), help='input annotation file in .json file', required=True)
parser.add_argument(
    '-o', '--output', type=str, default='output.lab', help='output file in .lab file (default output.lab)',
    required=True)

args = parser.parse_args()

infile = args.input.name
outfile = args.output
s = os.path.splitext("ddd.mp3")
if len(s) == 1:
    print("Output filename with audio extension is required (e.g., .wav, .mp3)")
    exit()
format = s[1][1:]

print("Processing %s\n" % infile)

with open(infile, 'r') as data_file:
    data = json.load(data_file)
    duration = float(data['duration'])
    all_beats = []
    all_chords = []
    process_parts(data['metre'], data, all_beats, all_chords, "chords")
    segments = merge_segments(to_beat_chord_segment_list(0, duration, all_beats, all_chords))

sample_rate=44100
end = max([x.end_time for x in segments])
res = np.zeros(int(sample_rate * end) + 1)

for s in segments:
    chord = np.array(generate_shepard_tone(
        freqs=symbol_to_frequencies(s.symbol),
        dur=s.end_time - s.start_time,
        Fs=sample_rate,
        amp=0.8))
    start_pos = int(sample_rate * s.start_time)
    res[start_pos:start_pos + len(chord)] = chord[0:]

ess.MonoWriter(filename=outfile, format=format)(res)

print("Sonification is written to ", outfile)
