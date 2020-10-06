import os
import argparse
from pychord_tools.common_utils import json_to_lab


def get_args():
    parser = argparse.ArgumentParser(
        description='Converts directory of .json files to MIREX .lab files')
    parser.add_argument(
        '-c', '--choose', type=str, default='chords', help='choose information to extract (options: chords/keys)',
        action='store', choices=['chords', 'keys'])
    parser.add_argument(
        '-i', '--input', type=str, default='annotations', help='input directory (with .json files)')
    parser.add_argument(
        '-o', '--output', type=str, default='labs', help='output directory')
    args = parser.parse_args()
    choice = args.choose
    infile = args.input
    outfile = args.output

    return choice, infile, outfile


choice, in_dir, out_dir = get_args()
for f in [os.path.join(in_dir, x) for x in os.listdir(in_dir)]:
    path, name = os.path.split(f)
    print(name)
    name, ext = os.path.splitext(name)
    json_to_lab(choice, f, os.path.join(out_dir, name + '.lab'))
