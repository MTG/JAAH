#!/bin/sh

# enable caching for pychord_tools
export PYCHORD_TOOLS_CACHE_DIR=$(pwd)/../.cache

export PYCHORD_TOOLS_PATH_DB_FILES=$(pwd)/../features/db.json
export PYTHONPATH=$(pwd):$PYTHONPATH
rm -r source
rm -r build
mkdir source
mkdir source/data
cp conf.py references.bib source/
python generate_rsts.py
make html
rm -r ../docs
cp -r build/html ../docs
touch ../docs/.nojekyll
