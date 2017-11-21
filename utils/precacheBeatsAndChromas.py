import os
import argparse
import numpy as np
import os.path as path
import lowLevelFeatures as ll
import time

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

parameters = ll.ChromaEvaluationParameters()
smoothingTimes = np.arange(0.25, 4.1, 0.25)

start = time.time()
with open(infile) as list_file:
    for line in list_file:
        jsonFile = str(path.realpath(line.rstrip()))
        audioFile = ll.extractAudioFileName(jsonFile)
        print "Caching beats for ", audioFile
        beatSegments = ll.rnnBeatSegments(audioFile)
        # chroma
        print "Caching chroma for ", audioFile
        chroma = ll.rawChromaFromAudio(
            audioFile, parameters.sampleRate, parameters.stepSize)
        print "Smoothing..."
        for st in smoothingTimes:
            ll.loadAnnotatedNNLSChromas(
                jsonFile,
                parameters.stepSize,
                st,
                parameters.rollToCRoot,
                parameters.sampleRate,
                chroma)
            ll.loadNNLSChromas(
                audioFile,
                parameters.stepSize,
                st,
                parameters.sampleRate,
                beatSegments.startTimes,
                beatSegments.durations,
                chroma)
        print "Time spent: ", time.time() - start
