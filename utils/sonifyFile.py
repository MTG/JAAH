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
resultfile = os.path.join(eval_dir, name + ".wav")
json2lab(infile, labfile)
sonifyCommand =\
    "sonify('" + labfile.replace("'", "''")  +\
    "', '" + audiofile.replace("'", "''") +\
    "', '" + resultfile.replace("'", "''") +"'); quit"
call([
'matlab',
'-nodesktop',
'-nosplash',
'-nojvm',
'-r',
sonifyCommand
])

print "Sonification is written to ", resultfile
