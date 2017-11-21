import os
import sys
from commonUtils import json2lab
from subprocess import call
import json
import argparse
import chordUtils
import essentia.standard
import vamp
import numpy as np
import re
import pandas as pd
import math

import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter

import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np

from sklearn import datasets
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import StratifiedKFold
from scipy.misc import logsumexp
from sklearn import preprocessing
from sklearn.model_selection import KFold
from sklearn import linear_model, datasets
from sklearn.model_selection import cross_val_score
from sklearn import svm
from sklearn.ensemble import RandomForestClassifier

sns.set(style="white", context="talk")
degrees=['I', 'IIb', 'II', 'IIIb', 'III', 'IV', 'Vb', 'V', 'VIb', 'VI', 'VIIb', 'VII']

def logNormalize(chromas):
    #data=preprocessing.normalize(chromas)
    data=np.log(preprocessing.normalize(chromas))
    # '/1000' is a hack in order to eliminate zero deviation.
    data[data < -2.0] = data[data < -2.0]/10000.0-5
    data[np.isnan(data)] = -5
    data[np.isinf(data)] = -5

    return data
def fitMixture(data, max_components=40, min_components=1):
    bic = 1000000
    bic_i = 0
    for i in range(min_components, max_components):
        gm = GaussianMixture(
            n_components=i, covariance_type='full',
            max_iter=200,
            random_state=8)
        gm.fit(data)
        curBic = gm.bic(data)
        print i, curBic, gm.converged_
        if (curBic < bic):
            bic = curBic
            bic_i = i
            # print gm.weights_
    gm = GaussianMixture(
        n_components=bic_i, covariance_type='full',
        max_iter=200,
        random_state=8)
    gm.fit(data)
    return gm

chromas, labels, kinds, mbids, start_times, durations = chordUtils.loadDatasetChroma('../out.npz')
chromas=logNormalize(chromas)
dMaj = pd.DataFrame(data=chromas[kinds == 'maj'], columns=degrees)
dMin = pd.DataFrame(data=chromas[kinds == 'min'], columns=degrees)
dDom = pd.DataFrame(data=chromas[kinds == 'dom'], columns=degrees)
dHdim = pd.DataFrame(data=chromas[kinds == 'hdim7'], columns=degrees)
dDim = pd.DataFrame(data=chromas[kinds == 'dim'], columns=degrees)
totalDuration = np.sum(durations)
majDuration=sum(durations[kinds == 'maj'])
minDuration=sum(durations[kinds == 'min'])
domDuration=sum(durations[kinds == 'dom'])
hdimDuration=sum(durations[kinds == 'hdim7'])
dimDuration=sum(durations[kinds == 'dim'])


print "Maj: ", len(dMaj), '(', len(dMaj) * 100.0 /len(chromas), '%) beats, ',majDuration,\
'(', majDuration*100.0/totalDuration, '%) sec'
print "Min: ", len(dMin), '(', len(dMin) * 100.0 /len(chromas), '%) beats, ',minDuration, 'sec',\
'(', minDuration*100.0/totalDuration, '%) sec'
print "Dom: ", len(dDom), '(', len(dDom) * 100.0 /len(chromas), '%) beats, ',domDuration, 'sec',\
'(', domDuration*100.0/totalDuration, '%) sec'
print "Hdim7: ", len(dHdim), '(', len(dHdim) * 100.0 /len(chromas), '%) beats, ',hdimDuration, 'sec',\
'(', hdimDuration*100.0/totalDuration, '%) sec'
print "Dim7: ", len(dDim), '(', len(dDim) * 100.0 /len(chromas), '%) beats, ',dimDuration, 'sec',\
'(', dimDuration*100.0/totalDuration, '%) sec'

unclassified = labels[kinds == 'unclassified']
Counter(unclassified).most_common(100)
#! normalize!!!
logreg = linear_model.LogisticRegression()
kf = KFold(n_splits=10, shuffle=True)
log_scores = cross_val_score(logreg, chromas, kinds, cv=kf)
# 74% crossvalidation (70% with new normalization)

#logreg.fit(chromas, kinds)
#logreg.score(chromas, kinds)

clf = svm.SVC(C=11, kernel = 'rbf', gamma=1.0)
#clf.fit(chromas, kinds)
#clf.score(chromas, kinds)
kf = KFold(n_splits=10, shuffle=True)
svm_scores = cross_val_score(clf, chromas, kinds, cv=kf, n_jobs=-1)
# 90% cross validation. (79% with normalization)
score = svm_scores.mean()
g_chromas, g_labels, g_kinds, g_mbids, g_start_times, g_durations = chordUtils.loadDatasetChroma('../guitar.npz')
g_chromas = np.log(g_chromas)
g_chromas[g_chromas < -0.25] = g_chromas[g_chromas < -0.25]/10000.0-5


# TODO: include estimation into this file.
# # GMM: 78% train error.
# TODO: variational EM
# TODO: RVM
# TODO: explore variational EM centroids: for "wrong" centroids,
# find samples with largest likelihood.
# Actually, GMM should work, we need better preprocessing.

# Tests + initialization: binary patterns, guitar chords. If not working: bad model!
