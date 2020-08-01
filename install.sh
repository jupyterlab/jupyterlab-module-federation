#!/bin/bash
set -ex
set -o pipefail

pip install setuptools pip --upgrade
pip install -v -e ".[test]"
jlpm && jlpm run build
pip install -e ./md_package
pip install -e ./middle_package
pip install -e ./theme_package
python labextensions.py develop md_package
python labextensions.py develop middle_package
python labextensions.py develop theme_package
