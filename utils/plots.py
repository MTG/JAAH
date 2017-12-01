from sklearn import preprocessing
import math
from collections import Counter
import matplotlib
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import numpy as np

degrees=['I', 'IIb', 'II', 'IIIb', 'III', 'IV', 'Vb', 'V', 'VIb', 'VI', 'VIIb', 'VII']

class TernaryDensity :
    def __init__(self, steps = 10):
        self.steps = steps
        self.triangles = Counter()
        self.total = 0

    def triangleID(self, x, y, z):
        xi = int(float(self.steps) * x)
        yi = int(float(self.steps) * y)
        zi = int(float(self.steps) * z)
        return (xi, yi, zi)

    def addPoint(self, x, y, z):
        self.triangles[self.triangleID(x, y, z)] += 1
        self.total += 1

    def triangleValue(self, n):
        return float(self.triangles[n]) / self.total

    def toScreenXY(self, triple):
        return [0.5 * (2 * triple[1] + triple[2]) / sum(triple),
                0.5 * math.sqrt(3.0) * triple[2] / sum(triple)]

    def patchCollection(self, x0 = 0.5, y0 = math.sqrt(3)/2, angle = -4.0 * math.pi / 3.0, gap=0.0):
        # working in 3D coordinates
        triangles = []
        for i in xrange(self.steps):
            xi = float(i) / self.steps
            line1=[]
            for j in xrange(self.steps - i + 1):
                yi = float(j) / self.steps
                line1.append([xi, yi, 1.0 - xi - yi])
            line2=[]
            xi += 1.0 / self.steps
            for j in xrange(self.steps - i):
                yi = float(j) / self.steps
                line2.append([xi, yi, 1.0 - xi - yi])
            # line 1 triangles
            for i in xrange(len(line1) - 1):
                triangles.append([line1[i], line1[i + 1], line2[i]])
            # line 2 triangles
            for i in xrange(len(line2) - 1):
                triangles.append([line2[i], line2[i + 1], line1[i + 1]])
        # TODO: shift & other transforms: rotate/compress(?)
        # b = [self.x1, self.y1]
        patches = []
        colors = np.empty(len(triangles))
        i = 0
        initialShift = np.array([gap, gap])
        b = np.array([x0, y0])
        c = math.cos(angle)
        s = math.sin(angle)
        r = np.array([[c, -s], [s, c]])
        for triangle in triangles:
            x = np.array(
                [self.toScreenXY(triangle[0]),
                 self.toScreenXY(triangle[1]),
                 self.toScreenXY(triangle[2])])
            x += initialShift
            x = x.dot(r)
            x += b
            polygon = Polygon(x, True)
            center = np.average(triangle, axis=0)
            id = self.triangleID(center[0], center[1], center[2])
            patches.append(polygon)
            colors[i] = self.triangles[id]
            i += 1
        p = PatchCollection(patches, facecolor='orange', cmap=matplotlib.cm.jet, alpha=1.0)
        p.set_array(colors)
        return p

def degreesTernaryPlot(ax, chroma, d1, d2, d3, stepsResilution = 50,
                           x0 = 0.5, y0 = math.sqrt(3)/2, angle = 2 * math.pi / 3.0, gap=0.0):
    d = preprocessing.normalize(chroma[:, (degrees.index(d1), degrees.index(d2), degrees.index(d3))], norm='l1')
    t = TernaryDensity(stepsResilution)
    for x in d:
        t.addPoint(x[0], x[1], x[2])
    ax.add_collection(t.patchCollection(x0, y0, angle, gap))

def plotLabels(ax, degrees, x0 = 0.5, y0 = math.sqrt(3)/2, angle = 2 * math.pi / 3.0, size = 15):
    x = np.zeros((len(degrees), 2), dtype='float64')
    x[0,:] = [0,0]
    v = np.array([1.0, 0.0])
    x[1, :] = v
    c = math.cos(-math.pi/3.0)
    s = math.sin(-math.pi/3.0)
    r = np.array([[c, -s], [s, c]])
    for i in xrange(2, len(degrees)):
        v = v.dot(r)
        x[i, :] = v
    b = np.array([x0, y0], dtype='float64')
    c = math.cos(angle)
    s = math.sin(angle)
    r = np.array([[c, -s], [s, c]])
    x = x.dot(r)
    x += b
    bbox_props = dict(boxstyle="circle", fc="w", ec="0.5", alpha=0.75)
    for i in xrange(len(degrees)):
        ax.text(x[i, 0], x[i, 1], degrees[i], ha="center", va="center", size=size,
            bbox=bbox_props)

def plotHexagram(ax, chroma, step = 30, gap = 0.005, labelSize = 12):
    ax.axes.set_xlim(-0.5, 1.5)
    ax.axes.set_ylim(0, 1.75)
    degreesTernaryPlot(ax, chroma, 'I', 'III', 'V', step, gap=gap)
    degreesTernaryPlot(ax, chroma, 'I', 'V', 'VII', step, angle=math.pi / 3.0, gap=gap)
    degreesTernaryPlot(ax, chroma, 'I', 'VII', 'VI', step, angle=0, gap=gap)
    degreesTernaryPlot(ax, chroma, 'I', 'VI', 'II', step, angle=-math.pi / 3.0, gap=gap)
    degreesTernaryPlot(ax, chroma, 'I', 'II', 'IV', step, angle=- 2.0 * math.pi / 3.0, gap=gap)
    degreesTernaryPlot(ax, chroma, 'I', 'IV', 'III', step, angle=- 3.0 * math.pi / 3.0, gap=gap)
    plotLabels(ax, ['I', 'III', 'V', 'VII', 'VI', 'II', 'IV'], size = labelSize)

def estimatePartition(partition, chromas):
    return np.sum(chromas[:, partition], axis=1)
