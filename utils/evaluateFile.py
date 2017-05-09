import os
import sys
from chordUtils import json2lab
from subprocess import call
import json

utils_path = os.path.dirname(os.path.realpath(__file__))
eval_dir = "evaluation"
data_root = os.environ['JAZZ_HARMONY_DATA_ROOT']
if not os.path.exists(eval_dir):
    os.mkdir(eval_dir)

try:
    infile = sys.argv[1]
except:
    print "usage:", sys.argv[0], "<input json file>"
    sys.exit()

with open(infile) as json_file:
    audiofile = json.load(json_file)['sandbox']['path'].replace('$JAZZ_HARMONY_DATA_ROOT', data_root)

audio_basename = os.path.basename(audiofile)
audio_name, audio_ext = os.path.splitext(audio_basename)

basename = os.path.basename(infile)
name, ext = os.path.splitext(basename)
labfile = os.path.join(eval_dir, name + ".lab")
json2lab('chords',infile, labfile)

# chordino
call(["sonic-annotator",
      "-t", utils_path + "/chords.n3",
       "-w", "lab",
      "--lab-basedir", eval_dir,
      "--lab-fill-ends",
      audiofile])

chordinoFile = os.path.join(eval_dir, audio_name + "_vamp_nnls-chroma_chordino_simplechord.lab")

with open(chordinoFile, 'r') as content_file:
    content = content_file.read().replace('"', '')
    os.remove(chordinoFile)
    chordinoFile = os.path.join(eval_dir, name + "_chordino.lab")
    with open(chordinoFile, 'w') as content_file:
        content_file.write(content)
outfile = os.path.join(eval_dir, name + "_chordino_MirexMajMin.txt")
call([
    'MusOOEvaluator',
    '--testfile', chordinoFile,
    '--reffile', labfile,
    '--chords', 'MirexMajMin',
    '--output', outfile])
call(['cat', outfile])
outfile = os.path.join(eval_dir, name + "_chordino_segmentation.txt")
call([
    'MusOOEvaluator',
    '--testfile', chordinoFile,
    '--reffile', labfile,
    '--segmentation', 'Inner',
    '--output', outfile])
call(['cat', outfile])

# TODO: madmom

# TODO: essentia


