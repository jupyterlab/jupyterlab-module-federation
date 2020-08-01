#!/bin/bash
set -ex
set -o pipefail

pip install setuptools pip --upgrade
pip install -v -e ".[test]"
jlpm && jlpm run build
pip install md_package
pip install middle_package
pip install theme_package
python labextensions.py develop md_package
python labextensions.py develop middle_package
python labextensions.py develop theme_package
