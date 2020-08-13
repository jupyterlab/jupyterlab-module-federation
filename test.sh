#!/bin/bash
set -ex
set -o pipefail

jupyter labextension list
python run.py

pip uninstall -y md_package
jupyter labextension uninstall @jupyterlab/federated-theme
