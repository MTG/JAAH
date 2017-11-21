import argparse
import json

from sklearn.model_selection import KFold
import numpy as np
import os

parser = argparse.ArgumentParser(
    description='Split file lists to folds for crossvalidation with train and test set')

parser.add_argument('infile', type=argparse.FileType('r'), help='txt input file (with list of json annotations)')
parser.add_argument('--folds', type=int, default=5, help='number of folds')
parser.add_argument('--dir', default='folds', help='Directory for generated lists')

args = parser.parse_args()
jsonList = args.infile.name
folds = args.folds
dir = args.dir

if not os.path.exists(dir):
    os.mkdir(dir)

mbids=[]
jsons=[]
with open(jsonList) as list_file:
    for line in list_file:
        json_file_name = line.rstrip()
        jsons.append(json_file_name)
        with open(json_file_name) as json_file:
            data = json.load(json_file)
            mbids.append(data['mbid'])

kf = KFold(n_splits=folds, shuffle=True, random_state=8)
pos = 1
for train_index, test_index in kf.split(jsons):
    trainFile = os.path.join(dir, 'trainFiles_' + str(pos) + '.txt')
    testFile = os.path.join(dir, 'testFiles_' + str(pos) + '.txt')
    trainMBIDs = os.path.join(dir, 'trainMBIDs_' + str(pos) + '.txt')
    testMBIDs = os.path.join(dir, 'testMBIDs_' + str(pos) + '.txt')
    with open(testFile, 'w') as tf:
        for i in test_index:
            tf.write(jsons[i] + '\n')
    with open(trainFile, 'w') as tf:
        for i in train_index:
            tf.write(jsons[i] + '\n')
    with open(testMBIDs, 'w') as tf:
        for i in test_index:
            tf.write(mbids[i] + '\n')
    with open(trainMBIDs, 'w') as tf:
        for i in train_index:
            tf.write(mbids[i] + '\n')
    pos += 1



