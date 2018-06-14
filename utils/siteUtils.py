import symbolicAnalysis
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import lowLevelFeatures as ll
from sklearn import preprocessing
import plots
import json
import recordingAttributes

def showTop2GramsForFileList(annotationFileList, top=100):
    symStatistics, topTwoGrams, topNGrams, matrix =\
        symbolicAnalysis.estimateStatistics(annotationFileList,
                                            top=top, maxNGram=20)
    twoGramsFrame = pd.DataFrame({'Bigrams': [x[0] for x in topTwoGrams], 'Qty': [x[1] for x in topTwoGrams]})
    fig = plt.figure(figsize=(18, int(25.0 * len(topTwoGrams) / 100)), dpi=90, facecolor='w', edgecolor='k')
    sns.set_color_codes("pastel")
    ax = sns.barplot("Qty", y="Bigrams", data=twoGramsFrame, color="b")
    ax.axes.set_xlabel("Quantity")
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    plt.tight_layout()
    plt.show()

def showTopNGramsForFileList(annotationFileList, top=100):
    symStatistics, topTwoGrams, topNGrams, matrix =\
        symbolicAnalysis.estimateStatistics(annotationFileList,
                                            top=top, maxNGram=20)
    nGramsFrame = pd.DataFrame({'N-grams': [x[0] for x in topNGrams], 'Qty': [x[1] for x in topNGrams]})
    fig = plt.figure(figsize=(20, int(25.0 * len(topNGrams) / 100)), dpi=90, facecolor='w', edgecolor='k')
    sns.set_color_codes("pastel")
    ax = sns.barplot("Qty", y="N-grams", data=nGramsFrame, color="b")
    ax.axes.set_xlabel("Quantity")
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    plt.tight_layout()
    plt.show()

def show5HexagramsForFileList(annotationFileList):
    cep = ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=1.2)
    chromaEvaluator = ll.AnnotatedChromaEvaluator(cep)
    chromas = chromaEvaluator.loadChromasForAnnotationFileList(annotationFileList)
    fig, ax = plt.subplots(nrows=1,ncols=5,figsize=(12,2.6), dpi= 90, facecolor='w', edgecolor='k')
    for axx in ax:
        axx.axes.get_xaxis().set_visible(False)
        axx.axes.get_yaxis().set_visible(False)
    ax[0].set_title("Maj")
    if (any(chromas.kinds == 'maj') > 0):
        maj = preprocessing.normalize(chromas.chromas[chromas.kinds == 'maj'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(maj,  columns=degrees), inner="point", ax=ax[0][0])
        plots.plotMajHexagram(ax[0], maj)
    ax[1].set_title("Min")
    if (any(chromas.kinds == 'min') > 0):
        min = preprocessing.normalize(chromas.chromas[chromas.kinds == 'min'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(min,  columns=degrees), inner="point", ax=ax[0][1])
        plots.plotMinHexagram(ax[1], min)
    ax[2].set_title("Dom")
    if (any(chromas.kinds == 'dom') > 0):
        dom = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dom'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(dom,  columns=degrees), inner="point", ax=ax[0][2])
        plots.plotDomHexagram(ax[2], dom)
    ax[3].set_title("Hdim7")
    if (any(chromas.kinds == 'hdim7') > 0):
        hdim7 = preprocessing.normalize(chromas.chromas[chromas.kinds == 'hdim7'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(hdim7,  columns=degrees), inner="point", ax=ax[0][3])
        plots.plotHdim7Hexagram(ax[3], hdim7)
    ax[4].set_title("Dim")
    if (any(chromas.kinds == 'dim') > 0):
        dim = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dim'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(dim,  columns=degrees), inner="point", ax=ax[0][4])
        plots.plotDimHexagram(ax[4], dim)
    plt.tight_layout()
    plt.show()

def showYearHistogramForFileList(annotationFileList):
    years = []
    for file in annotationFileList:
        with open(file, 'r') as df:
            annotation = json.load(df)
            print(file, annotation['mbid'])
            recording = recordingAttributes.loadRecordingAttributesFromMusicBrainz(
                annotation['mbid'])
            if (recording.started != None):
                years.append(int(recording.started[:4]))
    fig = plt.figure(figsize=(6, 4), dpi=90, facecolor='w', edgecolor='k')
    plt.hist(years)
    plt.xlabel('Year')
    plt.ylabel('Number of recordings')
    plt.show()
