import chordUtils
import pandas as pd

import seaborn as sns

import matplotlib.pyplot as plt

import numpy as np

from sklearn.mixture import GaussianMixture
from sklearn import preprocessing
from sklearn.model_selection import KFold

sns.set(style="white", context="talk")
degrees = ['I', 'IIb', 'II', 'IIIb', 'III', 'IV', 'Vb', 'V', 'VIb', 'VI', 'VIIb', 'VII']
allkinds = np.array(['maj', 'min', 'dom', 'hdim7', 'dim'])


def normalize(chromas, norm='l1'):
    data = chromas
    data = preprocessing.normalize(chromas, norm=norm)
    return data


def logNormalize(chromas):
    data = chromas
    data[data == 0] = np.exp(-10)
    data = np.log(preprocessing.normalize(chromas, norm='l1'))
    # data=preprocessing.normalize(chromas, norm='l1')

    # '/1000' is a hack in order to eliminate zero deviation.
    data[data < -10.0] = -10
    data[np.isnan(data)] = -10
    data[np.isinf(data)] = -10

    return data

def toLogRatio(chromaVector):
    res = np.zeros(11)
    product = 1.0
    for i in range(11):
        product = product * chromaVector[i]
        ii = i + 1.0
        res[i] = np.sqrt(ii / (ii + 1)) * np.log(product ** (1.0 / ii) / chromaVector[i + 1])
    return res

def imputeZeros(data):
    data[data == 0] = 0.0001
    return data

def normalizeTo11d(chromas) :
    c = preprocessing.normalize(imputeZeros(chromas), norm='l1')
    c = np.apply_along_axis(toLogRatio, 1, chromas)
    return c

def estimateBICs(data, min_components=1, max_components=40, covariance_type='full'):
    res = np.zeros(max_components - min_components + 1)
    for i in range(min_components, max_components + 1):
        gm = GaussianMixture(
            n_components=i, covariance_type=covariance_type,
            max_iter=200,
            random_state=8)
        gm.fit(data)
        curBic = gm.bic(data)
        res[i - 1] = curBic
        if (not gm.converged_):
            print i, curBic, gm.converged_
    return res


def findOptimalNComponentsByBIC(chromas, min_components=1, max_components=40, covariance_type='full'):
    fig, ax = plt.subplots(nrows=3, ncols=2)
    ax = np.reshape(np.array(ax), (1, np.size(ax)))[0]
    res = np.zeros(5)
    for i in xrange(5):
        chordname = allkinds[i]
        samples = chromas[kinds == chordname]
        bics = estimateBICs(samples, \
                            min_components=min_components, \
                            max_components=min(max_components, len(samples)),\
                            covariance_type=covariance_type)
        ax[i].set_title(chordname)
        ax[i].plot(bics)
        minIndex = np.argmin(bics)
        print chordname, "BIC: ", bics[minIndex], " N: ", minIndex + 1
        res[i] = minIndex + 1
    plt.show()
    return res


def fitMixture(data, n_components=1, covariance_type='full'):
    gm = GaussianMixture(
        n_components=n_components, covariance_type=covariance_type,
        max_iter=200,
        random_state=8)
    gm.fit(data)
    return gm


def removeUnclassified(list):
    (chromas, labels, kinds, mbids, start_times, durations) = list
    return (chromas[kinds != 'unclassified'], \
            labels[kinds != 'unclassified'], \
            kinds[kinds != 'unclassified'], \
            mbids[kinds != 'unclassified'], \
            start_times[kinds != 'unclassified'], \
            durations[kinds != 'unclassified'])


def kinds2nums(kinds):
    num = lambda x: np.where(allkinds == x)[0][0]
    return np.array([num(x) for x in kinds])


def nums2kinds(nums):
    return np.array([allkinds[x] for x in nums])


def fitConstModel(kinds, chromas, numbersOfComponents, covariance_type='full'):
    dMaj = pd.DataFrame(data=chromas[kinds == 'maj'])
    dMin = pd.DataFrame(data=chromas[kinds == 'min'])
    dDom = pd.DataFrame(data=chromas[kinds == 'dom'])
    dHdim = pd.DataFrame(data=chromas[kinds == 'hdim7'])
    dDim = pd.DataFrame(data=chromas[kinds == 'dim'])
    majGMM = fitMixture(dMaj.values, n_components=numbersOfComponents[0], covariance_type=covariance_type)
    minGMM = fitMixture(dMin.values, n_components=numbersOfComponents[1], covariance_type=covariance_type)
    domGMM = fitMixture(dDom.values, n_components=numbersOfComponents[2], covariance_type=covariance_type)
    hdimGMM = fitMixture(dHdim.values, n_components=numbersOfComponents[3], covariance_type=covariance_type)
    dimGMM = fitMixture(dDim.values, n_components=numbersOfComponents[4], covariance_type=covariance_type)
    return (majGMM, minGMM, domGMM, hdimGMM, dimGMM)


def chordScore(model, kinds, chroma):
    (majGMM, minGMM, domGMM, hdimGMM, dimGMM) = model
    return np.array([ \
        majGMM.score_samples(chroma), \
        minGMM.score_samples(chroma), \
        domGMM.score_samples(chroma), \
        hdimGMM.score_samples(chroma), \
        dimGMM.score_samples(chroma)])


def score(model, kinds, chromas, debug=False):
    scores = chordScore(model, kinds, chromas)
    p = np.argmax(scores, axis=0)
    for i in xrange(5):
        chordname = allkinds[i]
        pc = p[kinds == chordname]
        if (debug):
            print chordname, 100.0 * sum(pc == i) / len(pc), "%"
    nums = kinds2nums(kinds)
    score = 100.0 * sum(p == nums) / len(nums)
    if (debug):
        print 'total: ', score, '%'
    return score


def trainTestModel(kinds, chromas, numbersOfComponents, debug=False, nfolds=5, covariance_type='full'):
    kf = KFold(n_splits=nfolds, shuffle=True, random_state=8)
    testAcc = np.zeros(nfolds)
    trainAcc = np.zeros(nfolds)
    nfold = 0
    for train_index, test_index in kf.split(chromas):
        train_chromas = chromas[train_index]
        train_labels = labels[train_index]
        train_kinds = kinds[train_index]
        train_mbids = mbids[train_index]
        train_start_times = start_times[train_index]
        train_durations = durations[train_index]
        test_chromas = chromas[test_index]
        test_labels = labels[test_index]
        test_kinds = kinds[test_index]
        test_mbids = mbids[test_index]
        test_start_times = start_times[test_index]
        test_durations = durations[test_index]
        model = fitConstModel(train_kinds, train_chromas, numbersOfComponents, covariance_type=covariance_type)
        trainAcc[nfold] = score(model, train_kinds, train_chromas, debug)
        testAcc[nfold] = score(model, test_kinds, test_chromas, debug)
        if (debug):
            print trainAcc[nfold], testAcc[nfold]
        nfold += 1
    return (np.average(trainAcc), np.average(testAcc))


def trainTestSymmetricalModels(kinds, chromas, n_components=np.arange(1, 6), debug=False, covariance_type='full'):
    testAcc = np.zeros(len(n_components))
    trainAcc = np.zeros(len(n_components))
    i = 0
    for c in n_components:
        ncomp = np.ones(5, dtype=int) * int(c)
        (train, test) = trainTestModel(kinds, chromas, ncomp, nfolds=5, debug=debug, covariance_type=covariance_type)
        trainAcc[i] = train
        testAcc[i] = test
        i = i + 1
    return trainAcc, testAcc

chromas, labels, kinds, mbids, start_times, durations = removeUnclassified(chordUtils.loadDatasetChroma('./chroma275.npz'))
sxChromas = normalizeTo11d(chromas)
model = fitConstModel(kinds, sxChromas, [1,1,1,1,1], covariance_type='spherical')
score(model, kinds, sxChromas, debug=True)

from sklearn.externals import joblib
joblib.dump(model, 'gauss275log-ratio-sphere.pkl')
