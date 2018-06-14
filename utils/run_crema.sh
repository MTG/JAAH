#!/bin/sh
# $1 audio file
# $2 output directory
# $3 name
# $4 ext
export CREMA_PATH="/Users/seffka/Desktop/JazzHarmony/crema"
export JAMS_CMD="/Users/seffka/Desktop/JazzHarmony/jams/scripts/jams_to_lab.py"
unset PYTHONPATH
if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi
pyenv shell 3.5.1
PYTHONPATH=$CREMA_PATH:$PYTHONPATH
python3 -m crema.analyze "$1" -o "$2/$3.jams"
"$JAMS_CMD" "$2/$3.jams" "$2/$3"
grep -vE '(^#)|Time' "$2/$3__chord__00.lab" > "$2/$3.$4"
rm "$2/$3__chord__00.lab"
