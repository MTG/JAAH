import os
import jinja2
import json
from pychord_tools import recording_attributes
from pychord_tools import symbolic_analysis
from pychord_tools.labels import Jazz5LabelTranslator


def render_annotations(anno_directory, recording_template, out_dir, index_template, index_result):
    file_list = [os.path.join(anno_directory, x) for x in os.listdir(anno_directory)]
    last_year = 0
    first_year = 9999
    for file in file_list:
        with open(file, 'r') as df:
            annotation = json.load(df)
            print(file, annotation['mbid'])
            recording = recording_attributes.load_recording_attributes_from_music_brainz(
                annotation['mbid'])
            basename = os.path.basename(file)
            name, ext = os.path.splitext(basename)
            rstfile = os.path.join(out_dir, name + ".rst")
            sym_stat, top_two_grams, top_n_grams, transition_matrix = symbolic_analysis.estimate_statistics(
                [file], Jazz5LabelTranslator())
            #os.path.join('../', anno_directory)
            render(recording_template, file, basename, annotation, recording, sym_stat, rstfile)
            if recording.started is not None:
                year = int(recording.started[:4])
                last_year = max(year, last_year)
                first_year = min(year, first_year)
    # overall statistics
    sym_stat, top_two_grams, top_n_grams, transition_matrix = symbolic_analysis.estimate_statistics(
        file_list, Jazz5LabelTranslator())
    with open(index_result, 'w') as of:
        of.write(jinja2.Environment(
            loader=jinja2.FileSystemLoader('./')
        ).get_template(index_template).render(
            anno_directory=os.path.join('../', anno_directory),
            statistics=sym_stat,
            overview={'size': len(file_list), 'first_year': str(first_year), 'last_year': str(last_year)}))


def render(tpl_path, jsonpathname, jsonname, annotation, recording, statistics, out_file):
    path, filename = os.path.split(tpl_path)
    with open(out_file, 'w') as of:
        of.write(jinja2.Environment(
            loader=jinja2.FileSystemLoader(path or './')
        ).get_template(filename).render(
            jsonpathname=os.path.join('../../', jsonpathname),
            jsonname=jsonname,
            annotation=annotation,
            recording=recording,
            statistics=statistics))


if __name__ == '__main__':
    render_annotations(
        '../annotations',
        'recording_template.rst',
        'source/data',
        'index.rst',
        'source/index.rst')
