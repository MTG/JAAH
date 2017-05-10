#
# Example for fetching Music Brainz ID (MBID) and other basic properties and puting them into JSON
#
import json
import os
import re
import sys
import argparse
import numpy as np
from essentia.streaming import *

import acoustid
import musicbrainzngs as m

m.set_useragent("application", "0.01", "http://example.com")

API_KEY = 'cSpUJKpD'

def get_args():
    # Description for documentation
    parser = argparse.ArgumentParser(
        description='Extract metadata from musicbrainzid to .json file')
  
    parser.add_argument(
        '-p', '--path', type=str, help='Path to Audio files', required=True)
    parser.add_argument(
        '-m', '--mid', type=str, help='MusicBrainzID', required=True)
    parser.add_argument(
        '-o', type=argparse.FileType('w'), default='draft.json', help='output file (default is: draft.json)')
    # Array for all arguments passed to script
    args = parser.parse_args()
    # Assign args to variables
    inputdir = args.path
    musicbrainzid = args.mid
    
    
    # Return all variable values
    return inputdir, musicbrainzid, args.o.name

def collectRecordingIds(d, result):
    if (type(d) is dict):
        for k in d.keys():
            if (k == 'track-list') :
                for r in d['track-list']:
                    result.add(r['recording']['id'])
            elif (type(d[k]) is list):
                for e in d[k]:
                    collectRecordingIds(e, result)
            else:
                collectRecordingIds(d[k], result)

def aidmatch(filename):
    try:
        results = acoustid.match(API_KEY, filename)
    except acoustid.NoBackendError:
        print "chromaprint library/tool not found"
        sys.exit(1)
    except acoustid.FingerprintGenerationError:
        print "fingerprint could not be calculated"
        sys.exit(1)
    except acoustid.WebServiceError as exc:
        print "web service request failed:", exc.message
        sys.exit(1)
    return results

def extractTuningAndDuration(infile):
    chordHopSize = 2048
    frameSize = 8192
    loader = MonoLoader(filename=infile)
    framecutter = FrameCutter(hopSize=chordHopSize, frameSize=frameSize)
    windowing = Windowing(type="blackmanharris62")
    spectrum = Spectrum()
    spectralpeaks = SpectralPeaks(orderBy="frequency",
                                  magnitudeThreshold=1e-05,
                                  minFrequency=40,
                                  maxFrequency=5000,
                                  maxPeaks=10000)
    tuning = TuningFrequency()
    duration = Duration()
    # use pool to store data
    pool = essentia.Pool()
    # connect algorithms together
    loader.audio >> framecutter.signal
    loader.audio >> duration.signal
    framecutter.frame >> windowing.frame >> spectrum.frame
    spectrum.spectrum >> spectralpeaks.spectrum
    spectralpeaks.magnitudes >> tuning.magnitudes
    spectralpeaks.frequencies >> tuning.frequencies
    tuning.tuningFrequency >> (pool, 'tonal.tuningFrequency')
    tuning.tuningCents >> (pool, 'tonal.tuningCents')
    duration.duration >> (pool, 'duration.duration')
    # network is ready, run it
    print 'Processing audio file...', infile
    essentia.run(loader)
    return np.average(pool['tonal.tuningFrequency']), pool['duration.duration']


######################################################################

inputDir, musicbrainzid, outfile = get_args()
print inputDir, musicbrainzid, outfile

ids = set()

recordingsSet = set()
release =  m.get_release_by_id(musicbrainzid, includes=['recordings'])
collectRecordingIds(release, recordingsSet)


data_root = os.environ['JAZZ_HARMONY_DATA_ROOT']

res = []
for path, dname, fnames in os.walk(inputDir):
    for fname in fnames:
        if re.search('(\.wav$)|(\.mp3$)|(\.flac$)', fname):
            pathname = '/'.join((path, fname))
            print pathname
            tuning, duration = extractTuningAndDuration(pathname)
            print tuning, duration
            for score, rid, title, artist in aidmatch(pathname):
                if (rid in recordingsSet and not rid in ids):
                    ids.add(rid)
                    entry = {}
                    entry['mbid'] = rid
                    entry['title'] = title
                    entry['artist'] = artist
                    entry['tuning'] =  round(tuning, 2)
                    entry['metre'] = '4/4'
                    entry['duration'] = round(duration, 2)
                    pathname = pathname.replace(data_root, '$JAZZ_HARMONY_DATA_ROOT/')
                    entry['sandbox'] = {'path':pathname, 'transcriptions':[], 'key':[]}
                    res.append(entry)
                    break;

json.dump(res, open(outfile,'w'), indent=True)
