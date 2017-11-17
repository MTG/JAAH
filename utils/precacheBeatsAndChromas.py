import os
import sys
from chordUtils import json2lab
from subprocess import call
import json
import argparse
import chordUtils
import numpy as np
import re

eval_dir = "evaluation"
data_root = os.environ['JAZZ_HARMONY_DATA_ROOT']
if not os.path.exists(eval_dir):
    os.mkdir(eval_dir)

parser = argparse.ArgumentParser(
    description='Cache chroma statistics on given dataset'
                ' (distribution by 5 basic chord types: maj, min, dom, dim, hdim7 + unclassified'
                ' JAZZ_HARMONY_CACHE_DIR environment variable is used to store cache')

parser.add_argument('infile', type=argparse.FileType('r'), help='txt input file (with list of json annotations)')

args = parser.parse_args()

infile = args.infile.name

labels=np.array([], dtype='object')
kinds=np.array([], dtype='object')
chromas=np.zeros((0,12), dtype='float32')
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
