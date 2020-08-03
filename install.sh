#!/bin/bash
set -ex
set -o pipefail

pip install --user setuptools pip --upgrade
pip install -e ".[test]"
jlpm && jlpm run build
pip install -e ./json_package
pip install -e ./md_package
pip install -e ./middle_package
pip install -e ./theme_package
python labextensions.py develop json_package
python labextensions.py develop middle_package
python labextensions.py develop theme_package
