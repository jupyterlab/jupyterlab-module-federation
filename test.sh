#!/bin/bash
set -ex
set -o pipefail

jupyter labextensions list
python run.py

pip uninstall -y md_package
jupyter labextensions uninstall @jupyterlab/federated-theme
