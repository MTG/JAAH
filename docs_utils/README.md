# Utilities for building the documantation site.

Run build_docs.sh to rebuild the documentation.

Requirements:

   * Sphinx
   * pychord_tools (https://github.com/seffka/pychord_tools)
   * jinja2
   * matplotlib
   * seaborn
   * pandas
   * sklearn 
   
   Audio or/and pre-extracted chroma features should be available.
   PYCHORD_TOOLS_PATH_DB_FILES environment variable should contain absolute pathes to files with MBID to audio or chroma files mappig.
   E.g., db.json from ../features directory could be used.
   
   Mapping file for the audio on a local disk could be produced with "python -m pychord_tools.fill_audio_db  -p \<root directory with audio\> -o \<output file name\>".

   In order to make things faster, PYCHORD_TOOLS_CACHE_DIR shoucl be set to some directory to store cache files.
