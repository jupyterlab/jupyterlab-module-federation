#!/bin/bash
set -ex
set -o pipefail

pip install --user setuptools pip --upgrade
pip install -e ".[test]"
jlpm 
cat json_package/node_modules/.bin/build-labextension
jlpm run build
pip install -e ./json_package
pip install -e ./middle_package
pip install -e ./theme_package
jupyter labextension develop --overwrite json_package
jupyter labextension develop --overwrite middle_package
jupyter labextension develop --overwrite theme_package
cd md_package
jlpm run install-ext
