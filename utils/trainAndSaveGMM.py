import chordModel
import lowLevelFeatures as ll

model = chordModel.trainBasicChordGMM(
    ll.ChromaEvaluationParameters(stepSize=2048, smoothingTime=2.75),
    chordModel.BasicGMMParameters(norm='l1', preprocessing='log-ratio'),
    'ready.txt')
model.saveModel('utils/gauss275log-ratio-sphere.pkl')
