import cacher
import musicbrainzngs as mb


class RecordingAttributes :
    def __init__(self, title, artist, year, started, finished, lineup, composers):
        self.title = title
        self.artist = artist
        self.year = year
        self.started = started
        self.finished = finished
        self.lineup = lineup
        self.composers = composers

    def __str__(self):
        return u' '.join([
            self.title,
            self.artist,
            str(self.year),
            str(self.started),
            str(self.finished),
            str(self.lineup),
            str(self.composers)]).encode('utf-8')
    __repr__ = __str__


def extractComposersOtherwiseWriters(relationList):
    """
    Returns list of work's composers names (or writers, if there's no one composer).
    :param attrMap: musicBrainz  work relation list
    :return: array of strings (composers names)
    """
    composers = []
    writers = []
    for rel in relationList:
        if (rel['type'] == 'composer'):
            composers.append(rel['artist']['name'])
        elif (rel['type'] == 'writer'):
            writers.append(rel['artist']['name'])
    if (len(composers) > 0):
        return composers
    else:
        return writers


def getComposers(workRelatios):
    for workRel in workRelatios:
        if (workRel['type'] == 'performance'):
            workId = workRel['work']['id']
            workAttrs = mb.get_work_by_id(
                id=workId,
                includes=['artist-rels'])
            if ('artist-relation-list' in workAttrs['work'].keys()):
                return extractComposersOtherwiseWriters(
                    workAttrs['work']['artist-relation-list'])
    return []


def getLineup(artistRelations):
    result = {}
    for rel in artistRelations:
        if (rel['type'] == 'instrument'):
            key = u' and '.join(rel['attribute-list']).encode('utf-8')
            result.setdefault(key, []).append(rel['artist']['name'])
    return result


def estimateRecordingTime(artistRelations):
    beginDate = None
    endDate = None
    for rel in artistRelations:
        if ('begin' in rel.keys() and (beginDate == None or beginDate > rel['begin'])):
            beginDate = rel['begin']
        if ('end' in rel.keys() and (endDate == None or endDate < rel['end'])):
            endDate = rel['end']
    if (beginDate != None):
        year = beginDate[:4]
    else:
        year = None
    return beginDate, endDate, year


@cacher.memory.cache
def loadRecordingAttributesFromMusicBrainz(mbid):
    """
    Loads attributes for the single recording.
    :param mbid: MBID
    :return: RecordingAttributes
    """
    mb.set_useragent("application", "0.01", "http://example.com")
    recAttrs = mb.get_recording_by_id(
        id=mbid,
        includes=['artist-credits', 'artist-rels', 'work-rels'])
    lineup = {}
    composers = []
    recordingStarted = None
    recordingFinished = None
    recordingYear = None
    if ('artist-relation-list' in recAttrs['recording'].keys()):
        artistRelations = recAttrs['recording']['artist-relation-list']
        recordingStarted, recordingFinished, recordingYear = estimateRecordingTime(artistRelations)
        lineup = getLineup(artistRelations)
    if ('work-relation-list' in recAttrs['recording'].keys()):
        composers = getComposers(recAttrs['recording']['work-relation-list'])
    return RecordingAttributes(
        recAttrs['recording']['title'],
        recAttrs['recording']['artist-credit-phrase'],
        recordingYear,
        recordingStarted,
        recordingFinished,
        lineup,
        composers)


def loadDictFromMusicBrainz(mbids):
    """
    Loads recording attributes from musicbrainz DB
    for multiple mbids.
    :param mbids: array of musicbrainz ids.
    :return: dictionary mbid -> RecordingAttributes
    """
    result = {}
    for mbid in mbids:
        result[mbid] = loadRecordingAttributesFromMusicBrainz(mbid)
    return result
