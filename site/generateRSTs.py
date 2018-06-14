import os
import jinja2
import json
import recordingAttributes
import commonUtils
import symbolicAnalysis

def renderAnnotaions(fileListName, recordingTemplate, outDir, indexTemplate, indexResult):
    if __name__ == '__main__':
        fileList = commonUtils.loadFileList(fileListName)
        lastYear = 0
        firstYear = 9999
        for file in fileList:
            with open(file, 'r') as df:
                annotation = json.load(df)
                print(file, annotation['mbid'])
                recording = recordingAttributes.loadRecordingAttributesFromMusicBrainz(
                    annotation['mbid'])
                basename = os.path.basename(file)
                name, ext = os.path.splitext(basename)
                rstfile = os.path.join(outDir, name + ".rst")
                symStat, topTwoGrams, topNGrams, transitionMatrix = symbolicAnalysis.estimateStatistics([file])
                render(recordingTemplate, '../../../', file, basename, annotation, recording, symStat, rstfile)
                if (recording.started != None):
                    year = int(recording.started[:4])
                    lastYear = max(year, lastYear)
                    firstYear = min(year, firstYear)
        # overall statistics
        symStat, topTwoGrams, topNGrams, transitionMatrix = symbolicAnalysis.estimateStatistics(fileList)
        with open(indexResult, 'w') as of:
            of.write(jinja2.Environment(
                loader=jinja2.FileSystemLoader('./')
            ).get_template(indexTemplate).render(
                pathPrefix = '../../',
                fileListName = '../../' + fileListName,
                statistics = symStat,
                overview = {'size' : len(fileList), 'firstYear':str(firstYear), 'lastYear':str(lastYear)}))

def render(tpl_path, pathPrefix, jsonpathname, jsonname, annotation, recording, statistics, outFile):
    path, filename = os.path.split(tpl_path)
    with open(outFile, 'w') as of:
        of.write(jinja2.Environment(
            loader=jinja2.FileSystemLoader(path or './')
        ).get_template(filename).render(
            jsonpathname = pathPrefix + jsonpathname,
            jsonname = jsonname,
            annotation = annotation,
            recording = recording,
            statistics = statistics))


renderAnnotaions('ready.txt', 'site/recording_template.rst', 'site/source/data', 'site/index.rst', 'site/source/index.rst')
