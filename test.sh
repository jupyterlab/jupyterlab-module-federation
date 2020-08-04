#!/bin/bash
set -ex
set -o pipefail

python labextensions.py list
python run.py
jlpm run build:prod

pip uninstall -y md_package
python labextensions.py uninstall @jupyterlab/federated-theme
jlpm run clean:all
