import json
import argparse

def get_args():
    parser = argparse.ArgumentParser(
        description='convert input .json file to MIREX .lab file with beats')
    parser.add_argument(
        '-i', '--input', type=str, help='input annotation file in .json file', required=True)
    parser.add_argument(
        '-o', '--output', type=str, default='output.lab', help='output file in .lab file (default output.lab)',
        required=True)
    args = parser.parse_args()
    infile = args.input
    outfile = args.output

    return infile, outfile


def process_parts(data,  beatz = None):
    if 'parts' in data.keys():
        for part in data['parts']:
            process_parts(part, beatz)
    else:
        if beatz is not None:
            beatz.extend(data['beats'])

infile, outfile = get_args()

with open(infile, 'r') as data_file:
    data = json.load(data_file)
    duration = float(data['duration'])
    all_beats = []
    process_parts(data, all_beats)
    with open(outfile, 'w') as content_file:
        for s in all_beats:
            content_file.write(str(s) + '\n')
