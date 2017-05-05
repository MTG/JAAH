import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv
import argparse
import sys
from collections import Counter

## This script gets basic statistical information from the JazzCorpus.csv file and plots a 'barplot' for the index selected by user.


def get_args():
    # Description for documentation
    parser = argparse.ArgumentParser(
        description='Get Barplot of existing data in the JazzCorpus')
    parser.add_argument(
        '-p', '--path', type=str, help='Path to JazzCorpus', required=True)
    parser.add_argument(
        '-i', '--index', type=int, help='Column index : 0 - Musicbrainzid, 1 - Name of the Track, 2 - Artist, 5 - Accuracy with Chordino, 6 - Rhythm Feel, 7- Style, 8 - Orchestration, 9 - Instrumentation, 10 - Year of Recording', required=True)
    
    args = parser.parse_args()
    inputdir = args.path
    column_index = args.index
    return inputdir, column_index

inputdir, index = get_args()


with open(inputdir) as f:
    readdata = csv.reader(f, delimiter = ',')
    data=[]
    df=[]
    for row in readdata:
        splitElem = row[index]
        subElem = splitElem.split(' / ')
        for l in range(len(subElem)):
            df.append(subElem[l])
        data.append(row)
              
Header = data[0]
data.pop(0)
d = []
print Header
statname = df.pop(0)

for i in range(len(data)):
    d.append(str(data[i][index]))

###PLOTTING
    
labels, values = zip(*Counter(df).items())
indexes=np.arange(len(labels))


ax=plt.bar(indexes,values, width = 0.6)
ax=plt.style.use('fivethirtyeight')
width=0.6

plt.xticks(indexes + width * 0.5, labels, rotation = 'vertical')
plt.legend((statname,))



plt.ylabel('Quantity')
plt.xlabel('Index')
plt.title('Stats')

plt.show()
