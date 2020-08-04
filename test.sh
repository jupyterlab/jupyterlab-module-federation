#!/bin/bash
set -ex
set -o pipefail

python labextensions.py list
python run.py
jlpm run build:prod

pip uninstall md_package
python labextensions.py uninstall json_package
python labextensions.py uninstall middle_package
python labextensions.py uninstall theme_package
