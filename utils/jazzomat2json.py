""" Converts jazzomat sqlite database
to json annotation files with beats and chords.
"""

import argparse
import sqlite3
import json
import numpy as np
import commonUtils
import matplotlib.pyplot as plt
import collections
import re
import lowLevelFeatures as ll

harteTypeMapping = {
    u'j79#':'maj7(#9)',
    u'79#11#':'7(#, #11)',
    u'+7911#':'maj7(9,11)',
    u'j7':'maj7',
    u'79b13':'9(b13)',
    u'6911#':'maj6(9, #11)',
    u'7913':'9(13)',
    u'69':'maj6(9)',
    u'7911':'9(11)',
    u'-79b':'min(b9)',
    u'j79#11#':'maj7(#9, #11)',
    u'-69':'min6(9)',
    u'+':'aug',
    u'-':'min',
    u'-j7':'minmaj7',
    u'sus':'sus4',
    u'7':'7',
    u'6':'maj6',
    u'o7':'dim7',
    u'79#':'7(#9)',
    u'79#13':'9(#13)',
    u'+j7':'(3,#5,7)',
    u'7913b':'9(b13)',
    u'sus79':'sus(7,9)',
    u'+79b':'(3,#5,b7, b9)',
    u'7alt':'7(b5)',
    u'sus7':'sus(b7)',
    u'j7911#':'maj7(9, #11)',
    u'+79':'aug(7, 9)',
    u'79':'9',
    u'sus7913':'sus(b7, 9, 13)',
    u'j79':'maj7(9)',
    u'm7b5':'hdim7',
    u'-7913':'min7(9, 13)',
    u'-79':'min9',
    u'-j7913':'minmaj7(9,13)',
    u'o':'dim',
    u'-7':'min7',
    u'-6':'min6',
    u'+7':'aug(7)',
    u'79b':'7(b9)',
    u'+79#':'aug(7, #9)',
    u'-j7911#':'min7(9, #11)',
    u'79b13b':'7(b9, b13)',
    u'7911#':'9(#11)',
    u'-7911':'min7(9, 11)'
}

class JazzomatDB:
    def __init__(self, fileName):
        self.conn = sqlite3.connect(fileName)

    def fetchAll(self, query):
        c = self.conn.cursor()
        return c.execute(query).fetchall()

    def x(self, query):
        print(self.fetchAll(query))

    def desc(self, tablename):
        self.x("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = '%s'" % tablename)

    def solos(self):
        return self.fetchAll('SELECT s.melid, s.title, s.performer, s.trackid, s.solopart, s.signature, s.instrument, s.key, t.mbzid, tr.solostart_sec'
                             ' FROM solo_info s, track_info t, transcription_info tr'
                             ' WHERE t.trackid = s.trackid and tr.melid=s.melid')

    def sections(self, melid):
        return self.fetchAll(
            "SELECT type, start, end, value FROM sections WHERE melid = %d and (type = 'CHORUS' or type = 'FORM')" % melid)

    def beats(self, melid):
        return self.fetchAll(
            "SELECT beatid, onset, bar, beat, signature, chord, form, chorus_id FROM beats WHERE melid = %d order by  beatid" % melid)

    def events(self, melid):
        return self.fetchAll(
            "SELECT eventid, onset, duration, period, division, bar, beat, beatdur FROM melody WHERE melid = %d order by melid" % melid)

    def close(self):
        self.conn.close()

    def shiftTime(self, melid):
        c = self.conn.cursor()
        return c.execute("select solostart_sec from transcription_info where melid=%d" % melid).fetchone()[0]

    def startEnd(self, events, shift):
        onsets = [x[1] for x in events]
        durations = [x[2] for x in events]
        iMax = np.argmax(onsets)
        return np.min(onsets) + shift, onsets[iMax] + durations[iMax] + shift

    def beatTimestamps(self, melid):
        return np.array([x[1] for x in self.beats(melid)]) + self.shiftTime(melid)

class Section:
    def __init__(self, type, start, end, value):
        self.type = type
        self.value = value
        self.start = start
        self.end = end
        self.children = collections.OrderedDict()
        self.beats = []

class Beat:
    def __init__(self, onset, bar, beat, signature, chord, form, chorus):
        self.onset = onset
        self.bar = bar
        self.beat = beat
        self.signature = signature
        self.chord = chord
        self.form = form
        if (chorus == 0):
            chorus = -1
        self.chorus = unicode(str(chorus))

def beatTimestampsFromJSON(jsonFile):
    with open(jsonFile, 'r') as f:
        data = json.load(f)
        duration = data['duration']
        metreNumerator = int(data['metre'].split('/')[0])
        allBeats = []
        allChords = []
        commonUtils.processParts(metreNumerator, data, allBeats, allChords, 'chords')
        return np.array(allBeats)

def delta(a):
    return a[1:] - a[:len(a) - 1]

def allShifts(small, big):
    """Calculate shift for each beat for all possible offset
    """
    res = big[:len(small)] - small
    for i in range(1, len(big) - len(small)):
        res = np.vstack((res, big[i:len(small) + i] - small))
    return res

def alignInfo(jdb, melid, jsonFile):
    their = jdb.beatTimestamps(melid)
    ours = beatTimestampsFromJSON(jsonFile)
    shifts = allShifts(their, ours)
    deltaShifts = allShifts(delta(their), delta(ours))
    fig, ax = plt.subplots(nrows=4, ncols=1)
    means = np.mean(shifts, axis=1)
    stds = np.std(shifts, axis=1)
    meansDelta = np.mean(deltaShifts, axis=1)
    stdsDelta = np.std(deltaShifts, axis=1)
    ax[0].plot(abs(means))
    ax[1].plot(stds)
    ax[2].plot(abs(meansDelta))
    ax[3].plot(stdsDelta)
    plt.show()
    return their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta

def sectionDict(a):
    res = collections.OrderedDict(zip(a, range(len(a)))).keys()
    if (None in res):
        res.remove(None)
    return collections.OrderedDict([(section.value, section) for section in res])

degrees = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']

def degree(root, bass):
    rootN = ll.noteToNumber(root)
    bassN = ll.noteToNumber(bass)
    degree = bassN - rootN
    if (degree < 0):
        degree += 12
    return degrees[degree]

def harte(chord):
    if (chord == 'NC'):
        return 'N'
    else:
        r = re.search('^([ABCDEFG][b#]?)([^/]*)(/([ABCDEFG][b#]?))?$', chord)
        root = r.group(1)
        type = r.group(2)
        bass = r.group(4)
        allTypes.add(type)
        res = [root]
        if (type != ''):
            res.append(':')
            res.append(harteTypeMapping[type])
        if (bass != None):
            res.append('/')
            res.append(degree(root, bass))
    return ''.join(res)

def appendBar(res, bar, lastChord, beatsBySignature):
    if len(res) > 0 or bar[0].beat == 1 :
        res.append('|')
    chords = []
    beatN = []
    n = 0
    for b in bar:
        if b.chord == '':
            n += 1
        else:
            if n > 0:
                chords.append(lastChord)
                beatN.append(n)
            n = 1
            lastChord = b.chord
    if n > 0:
        chords.append(lastChord)
        beatN.append(n)

    if sum(beatN) == beatsBySignature and len(set(beatN)) <= 1 :
        for c in chords:
            res.append(harte(c))
            res.append(' ')
    else:
        for i in range(len(chords)):
            c = chords[i]
            n = beatN[i]
            for j in range(n):
                res.append(harte(c))
                res.append(' ')
    return lastChord

def chordsString(beats, beatsBySignature):
    res = []
    bar = []
    barId = None
    lastChord = 'NC'
    for b in beats:
        if barId != None and barId != b.bar :
            lastChord = appendBar(res, bar, lastChord, beatsBySignature)
            bar = []
        barId = b.bar
        bar.append(b)
    if len(bar) > 0:
        appendBar(res, bar, lastChord, beatsBySignature)
    if beats[-1].beat == beatsBySignature:
        res.append('|')
    return ''.join(res)

def makeParts(sections, instrument, shift, beatsBySignature):
    res = []
    for f in sections:
        formDict = {}
        if (f.type == u'CHORUS'):
            formDict['name'] = instrument + ' solo chorus ' + f.value
        else:
            formDict['name'] = f.value
        if (len(f.children) > 0):
            # print [c.value for c in f.children.values()]
            formDict['parts'] = makeParts(f.children.values(), instrument, shift, beatsBySignature)
        if (len(f.beats) > 0):
            formDict['beats'] = [b.onset + shift for b in f.beats]
            formDict['chords'] = [chordsString(f.beats, beatsBySignature)]
        res.append(formDict)
    return res

def fetchParts(jdb, melId, instrument, signature):
    """
    sections = [Section(raw[0], raw[1], raw[2], raw[3]) for raw in jdb.sections(melId)]
    maxId = max([s.end for s in sections])
    choruses = np.empty(maxId+1, dtype = 'object')
    forms = np.empty(maxId+1, dtype = 'object')
    for s in sections:
        if (s.type == u'CHORUS'):
            choruses[s.start:s.end+1] = np.repeat(s, s.end - s.start + 1)
        elif (s.type == u'FORM'):
            forms[s.start:s.end+1] = np.repeat(s, s.end - s.start + 1)
    chorusDict = sectionDict(choruses)
    for f in chorusDict.values():
        f.children = sectionDict(forms[f.start:f.end+1])
    """
    chorusDict = collections.OrderedDict()
    bs = jdb.beats(melId)
    formId = ''
    for b in bs:
        beat = Beat(*b[1:])
        if not beat.chorus in chorusDict:
            chorus = Section(u'CHORUS', beat.onset, None, beat.chorus)
            chorusDict[beat.chorus] = chorus
        chorus = chorusDict[beat.chorus]
        if (beat.form != ''):
            formId = beat.form
        if not formId in chorus.children:
            form = Section(u'FORM', beat.onset, None, formId)
            chorus.children[formId] = form
        form = chorus.children[formId]
        form.beats.append(beat)
    #print [c.value for c in chorusDict.values()]
    return makeParts(chorusDict.values(), instrument, jdb.shiftTime(melId), int(signature.split('/')[0]))

def convert2json(db, outDir):
    totalDuration = 0
    jdb = JazzomatDB(db)
    for (melid, title, performer, trackid, solopart, signature, instrument, key, mbid, solostart_sec) in jdb.solos():
        name = '_'.join([title, performer, str(solopart)]).replace(' ', '_').replace('\'', '_').replace('__', '_')
        res = {}
        # TODO: override from audio
        res['tuning'] = 440
        res['artist'] = performer
        res['title'] = title
        res['metre'] = signature
        res['sandbox'] = {}
        res['sandbox']['key'] = key.replace('-maj', '').replace('-min', ':min')
        res['mbid'] = mbid
        start, end = jdb.startEnd(jdb.events(melid), solostart_sec)
        res['start'] = start
        res['duration'] = end - start
        totalDuration += res['duration']
        beats = jdb.beats(melid)
        signatures = set(filter(lambda x: x != '', [b[4] for b in beats]))
        if (signature == '' or
                    len(signatures) > 1 or
                (len(signatures) == 1 and not (signature in signatures))) :
            print(name)
            print 'WARNING: solo signature: ', signature, ' beat signatures: ', signatures
            print 'entity is ignored (TODO: fix).'
            continue
        res['parts'] = fetchParts(jdb, melid, instrument, signature)
        json.dump(res, open(outDir + "/" + name + ".json",'w'), indent=True)
        print(name)
    return totalDuration

def shiftParts(parts, delta):
    for part in parts:
        if 'beats' in part:
            part['beats'] = (np.array(part['beats']) + delta).tolist()
        if 'parts' in part:
            shiftParts(part['parts'], delta)

def shiftAllData(data, delta):
    data['start'] = data['start'] + delta
    shiftParts(data['parts'], delta)
    return data


#####################################################################

parser = argparse.ArgumentParser(description='Convert jazzomat sqlite database to set of json files')

parser.add_argument('sqlite', help='jazzomat sqlite database .db file')
parser.add_argument('-o', dest = 'OUTDIR', default='.', help='output directory')

args = parser.parse_args()
db = args.sqlite
outDir = args.OUTDIR

allTypes = set()
totalDuration = convert2json(db, outDir)
print 'Jazzomat corpus duration:', totalDuration
print len(allTypes), allTypes
# db = '/Users/seffka/Jazzomat/wjazzd.db'
# jdb = JazzomatDB(db)
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 96, 'annotations/body_and_soul(hawkins).json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 53, 'annotations/blues_for_alice.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 177, 'annotations/walkin_shoes.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 191, 'annotations/blues_in_the_closet.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 397, 'annotations/blues_in_the_closet.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 222, 'annotations/giant_steps.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 223, 'annotations/giant_steps.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 379, 'annotations/blue_7.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 380, 'annotations/blue_7.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 381, 'annotations/blue_7.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 237, 'annotations/hotter_than_that.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 292, 'annotations/big_butter_and_eggman.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 385, 'annotations/st_thomas.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 386, 'annotations/st_thomas.json')
# their, ours, shifts, deltaShifts, means, stds, meansDelta, stdsDelta = alignInfo(jdb, 88, 'annotations/daahoud.json')


