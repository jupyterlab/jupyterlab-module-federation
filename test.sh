#!/bin/bash
set -ex
set -o pipefail

python labextensions.py list
python run.py

pip uninstall -y md_package
python labextensions.py uninstall @jupyterlab/federated-theme
