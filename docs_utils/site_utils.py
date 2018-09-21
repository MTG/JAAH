import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from sklearn import preprocessing
import json

from pychord_tools import symbolic_analysis
from pychord_tools import low_level_features as ll
from pychord_tools import plots
from pychord_tools import recording_attributes
from pychord_tools.labels import Jazz5LabelTranslator
from pychord_tools.third_party import NNLSChromaEstimator


def file_list(directory):
    return [os.path.abspath(os.path.join(directory, x)) for x in os.listdir(directory)]


def show_top_two_grams_for_file_list(annotation_file_list, top=100):
    sym_statistics, top_two_grams, top_n_grams, matrix = \
        symbolic_analysis.estimate_statistics(
            annotation_file_list,
            Jazz5LabelTranslator(),
            top=top, max_n_gram=20)
    two_grams_frame = pd.DataFrame({'Bigrams': [x[0] for x in top_two_grams], 'Qty': [x[1] for x in top_two_grams]})
    height = max(28.0 * int(len(top_two_grams) / 100), 3)
    fig = plt.figure(figsize=(18, height), dpi=90, facecolor='w', edgecolor='k')
    sns.set_color_codes("pastel")
    ax = sns.barplot("Qty", y="Bigrams", data=two_grams_frame, color="b")
    ax.axes.set_xlabel("Quantity")
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    plt.tight_layout()
    plt.show()


def show_top_n_grams_for_file_list(annotation_file_list, top=100):
    sym_statistics, top_two_grams, top_n_grams, matrix =\
        symbolic_analysis.estimate_statistics(
            annotation_file_list, Jazz5LabelTranslator(), top=top, max_n_gram=20)
    n_grams_frame = pd.DataFrame({'N-grams': [x[0] for x in top_n_grams], 'Qty': [x[1] for x in top_n_grams]})
    fig = plt.figure(figsize=(20, int(25.0 * len(top_n_grams) / 100)), dpi=90, facecolor='w', edgecolor='k')
    sns.set_color_codes("pastel")
    ax = sns.barplot("Qty", y="N-grams", data=n_grams_frame, color="b")
    ax.axes.set_xlabel("Quantity")
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    plt.tight_layout()
    plt.show()


def show_five_hexagrams_for_file_list(annotation_file_list):
    chroma_evaluator = ll.AnnotatedBeatChromaEstimator(
        chroma_estimator=NNLSChromaEstimator(),
        segment_chroma_estimator=ll.SmoothedStartingBeatChromaEstimator(smoothing_time=1.2),
        label_translator=Jazz5LabelTranslator())
    chromas = chroma_evaluator.load_chromas_for_annotation_file_list(annotation_file_list)
    fig, ax = plt.subplots(nrows=1,ncols=5,figsize=(12,2.6), dpi= 90, facecolor='w', edgecolor='k')
    for axx in ax:
        axx.axes.get_xaxis().set_visible(False)
        axx.axes.get_yaxis().set_visible(False)
    ax[0].set_title("Maj")
    if (any(chromas.kinds == 'maj') > 0):
        maj = preprocessing.normalize(chromas.chromas[chromas.kinds == 'maj'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(maj,  columns=degrees), inner="point", ax=ax[0][0])
        plots.plot_maj_hexagram(ax[0], maj)
    ax[1].set_title("Min")
    if (any(chromas.kinds == 'min') > 0):
        min = preprocessing.normalize(chromas.chromas[chromas.kinds == 'min'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(min,  columns=degrees), inner="point", ax=ax[0][1])
        plots.plot_min_hexagram(ax[1], min)
    ax[2].set_title("Dom")
    if (any(chromas.kinds == 'dom') > 0):
        dom = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dom'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(dom,  columns=degrees), inner="point", ax=ax[0][2])
        plots.plot_dom_hexagram(ax[2], dom)
    ax[3].set_title("Hdim7")
    if (any(chromas.kinds == 'hdim7') > 0):
        hdim7 = preprocessing.normalize(chromas.chromas[chromas.kinds == 'hdim7'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(hdim7,  columns=degrees), inner="point", ax=ax[0][3])
        plots.plot_hdim7_hexagram(ax[3], hdim7)
    ax[4].set_title("Dim")
    if (any(chromas.kinds == 'dim') > 0):
        dim = preprocessing.normalize(chromas.chromas[chromas.kinds == 'dim'], norm='l1')
        #sns.violinplot(data=pd.DataFrame(dim,  columns=degrees), inner="point", ax=ax[0][4])
        plots.plot_dim_hexagram(ax[4], dim)
    plt.tight_layout()
    plt.show()


def show_year_histogram_for_file_list(annotation_file_list):
    years = []
    for file in annotation_file_list:
        with open(file, 'r') as df:
            annotation = json.load(df)
            print(file, annotation['mbid'])
            recording = recording_attributes.load_recording_attributes_from_music_brainz(
                annotation['mbid'])
            if recording.started is not None:
                years.append(int(recording.started[:4]))
    fig = plt.figure(figsize=(6, 4), dpi=90, facecolor='w', edgecolor='k')
    plt.hist(years)
    plt.xlabel('Year')
    plt.ylabel('Number of recordings')
    plt.show()
