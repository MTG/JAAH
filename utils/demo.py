import plots
import lowLevelFeatures as ll
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import random
from sklearn import preprocessing
import matplotlib.pyplot as plt
from plots import degrees
import math
import chordModel
import numpy as np

cep = ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=1.2)
chromaEvaluator = ll.AnnotatedChromaEvaluator(cep)
chromas = chromaEvaluator.loadChromasForAnnotationFileListFile('ready.txt')
dMaj = pd.DataFrame(data=preprocessing.normalize(chromas.chromas[chromas.kinds == 'maj'], norm='l1'),  columns=degrees)
#g = sns.jointplot('VI', 'VII', dMaj, kind="kde")
maj = preprocessing.normalize(chromas.chromas[chromas.kinds == 'maj'], norm='l1')
fig, ax = plt.subplots()
plots.plotMajHexagram(ax, maj, 60)

# partition
partition = [degrees.index('I'), degrees.index('III'), degrees.index('V')]
a = plots.estimatePartition(partition, maj)
sns.distplot(a)
plt.show()

partition = [degrees.index('I'), degrees.index('II'), degrees.index('III'),  degrees.index('IV'), degrees.index('V'), degrees.index('VI'), degrees.index('VII')]
a = plots.estimatePartition(partition, maj)
sns.distplot(a)
plt.show()

partition = [degrees.index('V')]
a = plots.estimatePartition(partition, maj)
sns.distplot(a)
plt.show()

import scipy.stats as ss
b = ss.beta.fit(a, floc=0, fscale=1)


#guitar
#cep = ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=1.2)
#chromaEvaluator = ll.AnnotatedChromaEvaluator(cep)
guitar = chromaEvaluator.loadChromasForAnnotationFileListFile('guitar.txt')
gdMaj = pd.DataFrame(data=preprocessing.normalize(guitar.chromas[guitar.kinds == 'maj'], norm='l1'),  columns=degrees)
#g = sns.jointplot('VI', 'VII', dMaj, kind="kde")
gmaj = preprocessing.normalize(guitar.chromas[guitar.kinds == 'maj'], norm='l1')
fig, ax = plt.subplots()
plots.plotMajHexagram(ax, gmaj)

#dinah

#ax = np.reshape(np.array(ax), (1, np.size(ax)))[0]

fig, ax = plt.subplots(nrows=2,ncols=3)
django = chromaEvaluator.loadChromasForAnnotationFile('annotations/dinah.json')
djangoMaj = preprocessing.normalize(django.chromas[django.kinds == 'maj'], norm='l1')
ax[0][0].set_title("Django's Dinah major")
djangoFrame = pd.DataFrame(djangoMaj,  columns=degrees)
sns.violinplot(data=djangoFrame, inner="point", ax=ax[0][0])
plots.plotMajHexagram(ax[1][0], djangoMaj)

nichols = chromaEvaluator.loadChromasForAnnotationFile('annotations/dinah_red_nichols.json')
nicholsMaj = preprocessing.normalize(nichols.chromas[nichols.kinds == 'maj'], norm='l1')
ax[0][1].set_title("Red Nichol's Dinah major")
nicholsFrame = pd.DataFrame(nicholsMaj,  columns=degrees)
sns.violinplot(data=nicholsFrame, inner="point", ax=ax[0][1])
plots.plotMajHexagram(ax[1][1], nicholsMaj)

fats = chromaEvaluator.loadChromasForAnnotationFile('annotations/dinah_fats_waller.json')
fatsMaj = preprocessing.normalize(fats.chromas[fats.kinds == 'maj'], norm='l1')
ax[0][2].set_title("Fats Waller's Dinah major")
fatsFrame = pd.DataFrame(fatsMaj,  columns=degrees)
sns.violinplot(data=fatsFrame, inner="point", ax=ax[0][2])
plots.plotMajHexagram(ax[1][2], fatsMaj)

# guitar simple
import re
triads = guitar.chromas[[re.match('^[ABCDEFG][b#]?$', x) != None for x in guitar.labels]]
maj7 = guitar.chromas[[re.match('[ABCDEFG][b#]?:maj7', x) != None for x in guitar.labels]]
maj6 = guitar.chromas[[re.match('[ABCDEFG][b#]?:maj6', x) != None for x in guitar.labels]]
g69 = guitar.chromas[[re.match('[ABCDEFG][b#]?:\(3,6,9\)', x) != None for x in guitar.labels]]

fig, ax = plt.subplots(nrows=2,ncols=2)
ax[0, 0].set_title("Guitar triads")
plots.plotMajHexagram(ax[0, 0], triads, step=20)

ax[0, 1].set_title("Guitar maj7")
plots.plotMajHexagram(ax[0, 1], maj7, step=20)

ax[1, 0].set_title("Guitar maj6")
plots.plotMajHexagram(ax[1, 0], maj6, step=20)

ax[1,1].set_title("Guitar maj69 (without 5)")
plots.plotMajHexagram(ax[1, 1], g69, step=20)

plt.show()
#########

dinah = chromaEvaluator.loadChromasForAnnotationFile('annotations/cotton_tail.json')
dinahMaj = preprocessing.normalize(dinah.chromas[dinah.kinds == 'maj'], norm='l1')
dFrame = pd.DataFrame(dinahMaj,  columns=degrees)
fig, ax = plt.subplots(nrows=2,ncols=1)
ax[0].set_title("")
sns.violinplot(data=dFrame, inner="point", ax=ax[0])
plots.plotMajHexagram(ax[1], dinahMaj, step=20)

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, maj, 'V', 'VII', 'VI', 20)
plots.plotLabels(ax, ['V', 'VII', 'VI'])
plt.show()

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, maj, 'I', 'VII', 'VI', 20)
plots.plotLabels(ax, 'I', 'VII', 'VI')
plt.show()

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, maj, 'II', 'VII', 'VI', 15)
plots.plotLabels(ax, 'II', 'VII', 'VI')
plt.show()


fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, maj, 'I', 'III', 'V', 15)
plots.plotLabels(ax, 'I', 'III', 'V')
plt.show()


# Minor Chord
min = preprocessing.normalize(chromas.chromas[chromas.kinds == 'min'], norm='l1')
dMin = pd.DataFrame(data=preprocessing.normalize(min, norm='l1'),  columns=degrees)
sns.violinplot(data=dMin, inner="point")
plt.show()

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, min, 'I', 'IIIb', 'V', 60)
plots.plotLabels(ax, ['I', 'IIIb', 'V'])
plt.show()

def plotMin6bHexagram(ax, chroma, step = 30, gap = 0.005, labelSize = 12):
    ax.axes.set_xlim(-0.5, 1.5)
    ax.axes.set_ylim(0, 1.75)
    plots.degreesTernaryPlot(ax, chroma, 'I', 'IIIb', 'V', step, gap=gap)
    plots.degreesTernaryPlot(ax, chroma, 'I', 'V', 'VII', step, angle=math.pi / 3.0, gap=gap)
    plots.degreesTernaryPlot(ax, chroma, 'I', 'VII', 'VIb', step, angle=0, gap=gap)
    plots.degreesTernaryPlot(ax, chroma, 'I', 'VIb', 'II', step, angle=-math.pi / 3.0, gap=gap)
    plots.degreesTernaryPlot(ax, chroma, 'I', 'II', 'IV', step, angle=- 2.0 * math.pi / 3.0, gap=gap)
    plots.degreesTernaryPlot(ax, chroma, 'I', 'IV', 'IIIb', step, angle=- 3.0 * math.pi / 3.0, gap=gap)
    plots.plotLabels(ax, ['I', 'IIIb', 'V', 'VII', 'VIb', 'II', 'IV'], size = labelSize)

fig, ax = plt.subplots()
plotMin6bHexagram(ax, min, 60)
plt.show()

fig, ax = plt.subplots()
assert isinstance(ax, object)
plots.plotMinHexagram(ax, min, 60)
plt.show()

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, min, 'I', 'VIb', 'VI', 60)
plots.plotLabels(ax, ['I', 'VIb', 'VI'])

# Dominant
dom = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dom'], norm='l1')
dDom = pd.DataFrame(data=preprocessing.normalize(dom, norm='l1'),  columns=degrees)
sns.violinplot(data=dDom, inner="point")
plt.show()

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, dom, 'Vb', 'VIb', 'IIb', 60)
plots.plotLabels(ax, ['Vb', 'VIb', 'IIb'])
plt.show()

fig, ax = plt.subplots()
plots.plotDomHexagram(ax, dom, 60)
plt.show()

# Hdim7
hdim7 = preprocessing.normalize(chromas.chromas[chromas.kinds == 'hdim7'], norm='l1')
dHdim7 = pd.DataFrame(data=preprocessing.normalize(hdim7, norm='l1'),  columns=degrees)
sns.violinplot(data=dHdim7, inner="point")
plt.show()

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, hdim7, 'I', 'VIIb', 'IIIb')
plots.plotLabels(ax, ['I', 'VIIb', 'IIIb'])
plt.show()


fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, hdim7, 'IIb', 'V', 'VIb')
plots.plotLabels(ax, ['IIb', 'V', 'VIb'])
plt.show()

fig, ax = plt.subplots()
assert isinstance(ax, object)
plots.plotHdim7Hexagram(ax, hdim7, 30)
plt.show()

# dim
dim = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dim'], norm='l1')
dDim = pd.DataFrame(data=preprocessing.normalize(dim, norm='l1'),  columns=degrees)
sns.violinplot(data=dDim, inner="point")
plt.show()

fig, ax = plt.subplots()
plots.degreesTernaryPlot(ax, dim, 'I', 'IIIb', 'Vb', stepsResilution =30)
plots.plotLabels(ax, ['I', 'IIIb', 'Vb'])
plt.show()

fig, ax = plt.subplots()
assert isinstance(ax, object)
plots.plotDimHexagram(ax, dim, 30)
plt.show()


############ Comparisons
fig, ax = plt.subplots(nrows=2,ncols=2,figsize=(20, 17), dpi= 90, facecolor='w', edgecolor='k')
ms = chromaEvaluator.loadChromasForAnnotationFile('annotations/minor_swing.json')
msMin = preprocessing.normalize(ms.chromas[ms.kinds == 'min'], norm='l1')
ax[0][0].set_title("Django's Minor Swing minor")
msFrame = pd.DataFrame(msMin,  columns=degrees)
sns.violinplot(data=msFrame, inner="point", ax=ax[0][0])
plots.plotMinHexagram(ax[1][0], msMin)

dinah = chromaEvaluator.loadChromasForAnnotationFile('annotations/the_man_i_love.json')
dinahMin = preprocessing.normalize(dinah.chromas[dinah.kinds == 'min'], norm='l1')
ax[0][1].set_title("Django's Dinah minor")
dinahFrame = pd.DataFrame(dinahMin,  columns=degrees)
sns.violinplot(data=dinahFrame, inner="point", ax=ax[0][1])
plots.plotMinHexagram(ax[1][1], dinahMin)
plt.show()

## The 5chord picture

def plot5Chords(chromas):
    fig, ax = plt.subplots(nrows=2,ncols=5,figsize=(11.69,8.27), dpi= 90, facecolor='w', edgecolor='k')
    ax[0][0].set_title("Maj")
    if (any(chromas.kinds == 'maj') > 0):
        maj = preprocessing.normalize(chromas.chromas[chromas.kinds == 'maj'], norm='l1')
        sns.violinplot(data=pd.DataFrame(maj,  columns=degrees), inner="point", ax=ax[0][0])
        plots.plotMajHexagram(ax[1][0], maj)
    ax[0][1].set_title("Min")
    if (any(chromas.kinds == 'min') > 0):
        min = preprocessing.normalize(chromas.chromas[chromas.kinds == 'min'], norm='l1')
        sns.violinplot(data=pd.DataFrame(min,  columns=degrees), inner="point", ax=ax[0][1])
        plots.plotMinHexagram(ax[1][1], min)
    ax[0][2].set_title("Dom")
    if (any(chromas.kinds == 'dom') > 0):
        dom = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dom'], norm='l1')
        sns.violinplot(data=pd.DataFrame(dom,  columns=degrees), inner="point", ax=ax[0][2])
        plots.plotDomHexagram(ax[1][2], dom)
    ax[0][3].set_title("Hdim7")
    if (any(chromas.kinds == 'hdim7') > 0):
        hdim7 = preprocessing.normalize(chromas.chromas[chromas.kinds == 'hdim7'], norm='l1')
        sns.violinplot(data=pd.DataFrame(hdim7,  columns=degrees), inner="point", ax=ax[0][3])
        plots.plotHdim7Hexagram(ax[1][3], hdim7)
    ax[0][4].set_title("Dim")
    if (any(chromas.kinds == 'dim') > 0):
        dim = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dim'], norm='l1')
        sns.violinplot(data=pd.DataFrame(dim,  columns=degrees), inner="point", ax=ax[0][4])
        plots.plotDimHexagram(ax[1][4], dim)
    return fig, ax

# How to save pdf
from matplotlib.backends.backend_pdf import PdfPages
fig, ax = plot5Chords(chromas)
fig.suptitle("Jazz dataset chord's chroma distribution")
fig.subplots_adjust(bottom=0.33, top=0.85, left=0.05, right=0.98)
pp = PdfPages('all.pdf')
pp.savefig(fig)
pp.close()

# All Dinah
dinah = chromaEvaluator.loadChromasForAnnotationFile('annotations/dinah.json')
fig, ax = plot5Chords(dinah)
fig.suptitle("Django's Dinah chord's chroma distribution")
fig.subplots_adjust(bottom=0.33, top=0.85, left=0.05, right=0.98)

# ...
dinah = chromaEvaluator.loadChromasForAnnotationFile('annotations/girl_from_ipanema.json')
fig, ax = plot5Chords(dinah)
fig.suptitle("Girl from Ipanema chord's chroma distribution")
fig.subplots_adjust(bottom=0.33, top=0.85, left=0.05, right=0.98)
plt.show()


# Dirichlet demo
partition = [degrees.index('I'), degrees.index('II'), degrees.index('III'),  degrees.index('IV'), degrees.index('V'), degrees.index('VI'), degrees.index('VII')]
a = plots.estimatePartition(partition, maj)
sns.distplot(a)
plt.show()

fig, ax = plt.subplots()
plots.plotMajHexagram(ax, maj, step=60)
plt.show()

from scipy.stats import dirichlet
d = dirichlet.rvs([2,1,2,1,2,2,1,2,1,2,1,2], 20000)
d = dirichlet.rvs([1,1,1,1,1,1,1,1,1,1,1,1], 20000)

partition = [degrees.index('I'), degrees.index('II'), degrees.index('III'),  degrees.index('IV'), degrees.index('V'), degrees.index('VI'), degrees.index('VII')]
a = plots.estimatePartition(partition, d)
sns.distplot(a)
plt.show()

fig, ax = plt.subplots()
plots.plotMajHexagram(ax, d, step=60)
plt.show()


# fit beta
cep = ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=1.2)
chromaEvaluator = ll.AnnotatedChromaEvaluator(cep)
chromas = chromaEvaluator.loadChromasForAnnotationFileListFile('ready.txt')
#g = sns.jointplot('VI', 'VII', dMaj, kind="kde")
maj = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'maj']), norm='l1')
dMaj = pd.DataFrame(data=maj,  columns=degrees)

from scipy.stats import beta
partition = [degrees.index('I'), degrees.index('II'), degrees.index('III'),  degrees.index('IV'), degrees.index('V'), degrees.index('VI'), degrees.index('VII')]
a = plots.estimatePartition(partition, maj)
params = beta.fit(a, floc=0, fscale=1)

import numpy as np
import matplotlib.pyplot as plt
myHist = plt.hist(a, 60, normed=True)
rv = beta(*params)
x = np.linspace(0,1)
h = plt.plot(x, rv.pdf(x), lw=2)
h = plt.plot(x, rv.cdf(x), lw=2)

plt.show()

pp = [degrees.index('I'), degrees.index('II'), degrees.index('III'), degrees.index('V'), degrees.index('VI'), degrees.index('VII'), degrees.index('IV'), degrees.index('Vb'), degrees.index('VIb'), degrees.index('IIb'), degrees.index('VIIb'), degrees.index('IIIb')]
import numpy as np

# entropy/mean
cep = ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=1.2)
chromaEvaluator = ll.AnnotatedChromaEvaluator(cep)
chromas = chromaEvaluator.loadChromasForAnnotationFileListFile('ready.txt')
maj = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'maj']), norm='l1')
av = np.mean(maj, axis=0)
t = np.empty(len(degrees), dtype=[('degree', object), ('entropy', float), ('mean', float), ('ll', float)])
for i in xrange(len(degrees)):
    partition = [i]
    a = plots.estimatePartition(partition, maj)
    params = beta.fit(a, floc=0, fscale=1)
    e = beta.entropy(*params)
    ll = beta.logpdf(a, *params).sum()
    t[i] = (degrees[i], e, av[i], ll)
    print np.array(degrees)[partition], e, av[i], ll
t.sort(order='mean')
t.sort(order='entropy')
pp = t['degree']
#pp = np.flip(pp, axis=0)
pp = [degrees.index(x) for x in pp]

for i in xrange(11):
    partition = np.array(pp)[0:i+1]
    a = plots.estimatePartition(partition, maj)
    params = beta.fit(a, floc=0, fscale=1)
    e = beta.entropy(*params)
    print np.array(degrees)[partition], e*min(i+1, 12 - i -1), beta.logpdf(a, *params).sum()


import matplotlib.pyplot as plt
myHist = plt.hist(a, 60, normed=True)
rv = beta(*params)
x = np.linspace(0,1)
h = plt.plot(x, rv.pdf(x), lw=2)
h = plt.plot(x, rv.cdf(x), lw=2)

plt.show()

# sums...
60000 samples * 12 transpositions
count likelihood for 60 chords (???CDF)
11**5 splits

# weakest
cep = ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=1.2)
chromaEvaluator = ll.AnnotatedChromaEvaluator(cep)
chromas = chromaEvaluator.loadChromasForAnnotationFileListFile('ready.txt')
maj = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'maj']), norm='l1')
fig, ax = plt.subplots()
plots.plotHexagram(ax, maj, degrees = ['I', 'IIb', 'VIb', 'VIIb', 'Vb', 'IIIb', 'IV'], step=60)
plt.show()

# strongest
fig, ax = plt.subplots()
plots.plotHexagram(ax, maj, degrees = ['I', 'IV', 'II', 'VII', 'VI', 'III', 'V'], step=60)
plt.show()

# Min
min = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'min']), norm='l1')
print plots.sortedDegrees(min)
print plots.sortedDegrees(min, method='entropy')
print plots.sortedDegrees(min, method='beta-likelihood', flip=True)
entr = plots.sortedDegrees(min, method='entropy')
m = plots.sortedDegrees(min, method='mean')

fig, ax = plt.subplots(nrows=2,ncols=2)

plots.plotStrongWeakHexagrams(ax[0][0], ax[1][0], min, m, step = 60)
plots.plotStrongWeakHexagrams(ax[0][1], ax[1][1], min, entr, step = 60)

plt.show()


# Dom
dom = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'dom']), norm='l1')
print plots.sortedDegrees(dom)
print plots.sortedDegrees(dom, method='entropy')
print plots.sortedDegrees(dom, method='beta-likelihood', flip=True)
entr = plots.sortedDegrees(dom, method='entropy')
m = plots.sortedDegrees(dom, method='mean')

fig, ax = plt.subplots(nrows=2,ncols=2)

plots.plotStrongWeakHexagrams(ax[0][0], ax[1][0], dom, m, step = 60)
plots.plotStrongWeakHexagrams(ax[0][1], ax[1][1], dom, entr, step = 60)

plt.show()

# Hdim7
hdim7 = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'hdim7']), norm='l1')
print plots.sortedDegrees(hdim7)
print plots.sortedDegrees(hdim7, method='entropy')
print plots.sortedDegrees(hdim7, method='beta-likelihood', flip=True)
entr = plots.sortedDegrees(hdim7, method='entropy')
m = plots.sortedDegrees(hdim7, method='mean')

fig, ax = plt.subplots(nrows=2,ncols=2)

plots.plotStrongWeakHexagrams(ax[0][0], ax[1][0], hdim7, m, step = 60)
plots.plotStrongWeakHexagrams(ax[0][1], ax[1][1], hdim7, entr, step = 60)

plt.show()

# dim
dim = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'dim']), norm='l1')
print plots.sortedDegrees(dim)
print plots.sortedDegrees(dim, method='entropy')
print plots.sortedDegrees(dim, method='beta-likelihood', flip=True)
entr = plots.sortedDegrees(dim, method='entropy')
m = plots.sortedDegrees(dim, method='mean')

fig, ax = plt.subplots(nrows=2,ncols=2)

plots.plotStrongWeakHexagrams(ax[0][0], ax[1][0], dim, m, step = 60)
plots.plotStrongWeakHexagrams(ax[0][1], ax[1][1], dim, entr, step = 60)

plt.show()

# Generate 'major' samples.
# data from fold1
cep = ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=1.2)
chromaEvaluator = ll.AnnotatedChromaEvaluator(cep)
chromas = chromaEvaluator.loadChromasForAnnotationFileListFile('folds/trainFiles_1.txt')
maj = preprocessing.normalize(chordModel.substituteZeros(chromas.chromas[chromas.kinds == 'maj']), norm='l1')
print plots.sortedDegrees(maj)
print plots.sortedDegrees(maj, method='entropy')
print plots.sortedDegrees(maj, method='beta-likelihood', flip=True)
entr = plots.sortedDegrees(maj, method='entropy')
m = plots.sortedDegrees(maj, method='mean')

fig, ax = plt.subplots(nrows=2,ncols=2)

plots.plotStrongWeakHexagrams(ax[0][0], ax[1][0], maj, m, step = 60)
plots.plotStrongWeakHexagrams(ax[0][1], ax[1][1], maj, entr, step = 60)

plt.show()
# load model
model = chordModel.loadModel('folds/model_1.pkl')
gen,_= model.gmms[0].sample(20000)
# back to chroma
sampled = np.apply_along_axis(chordModel.invilr, 1, gen)
print plots.sortedDegrees(sampled)
print plots.sortedDegrees(sampled, method='entropy')
print plots.sortedDegrees(sampled, method='beta-likelihood', flip=True)
entr = plots.sortedDegrees(sampled, method='entropy')
m = plots.sortedDegrees(sampled, method='mean')
fig, ax = plt.subplots(nrows=1,ncols=2)

plots.plotStrongWeakHexagrams(ax[0], ax[1], sampled, m, step = 60)

plt.show()


# testing of inverse ilr
def f(i):
    c = np.ones(12)
    c[i] = 10
    c = chordModel.rescale(c)
    cc = chordModel.invilr(chordModel.ilr(c))
    plt.plot(c)
    plt.plot(cc)

for i in xrange(12):
    f(i)
plt.show()

c = np.ones(12)
c[0] = 10
c = chordModel.rescale(c)
cc = chordModel.invilr(chordModel.ilr(c))
plt.plot(c)
plt.plot(cc)
plt.show()


# evaluation of McFee's algorithm
# TODO: run McFee's
# run jams -> lab
# evaluate all files together and separately. Cache this data.
import validation
chordsFile, segmentationFile = validation.callMusOOEvaluatorForSingleFile(
                "tmp_mcfee_evaluation", "rag", 'lab', '5JazzFunctions', '/Users/seffka/Desktop/JazzHarmony/crema/qqq__chord__00.lab', '/Users/seffka/Desktop/JazzHarmony/JazzHarmonyCorpus/tmp_true_chords/maple_leaf_rag(hyman).lab')

validation.trainGMM_CV(trainingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2),gmmParams=chordModel.BasicGMMParameters(norm='l1', preprocessing='alr', covarianceTypes=np.repeat('full', chordModel.N_CHORD_KINDS)), modelPattern=validation.MODEL_ALR_PATTERN)
validation.trainGMM_CV(trainingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2),gmmParams=chordModel.BasicGMMParameters(norm=None, preprocessing=None, nComponents=21*np.ones(chordModel.N_CHORD_KINDS, dtype=int), covarianceTypes=np.repeat('full', chordModel.N_CHORD_KINDS)), modelPattern='folds' + '/' + "model_none_{0}.pkl")
res = validation.testCV(testingChromaParams = ll.ChromaEvaluationParameters(2048, 1.2), modelPattern='folds' + '/' + "model_none_{0}.pkl")
'folds' + '/' + "model_none_{0}.pkl"