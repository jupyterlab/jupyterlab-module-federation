# juptyerlab-module-federation

This repository is a temporary playground for implementing a new JupyterLab extension
system that utilizes the Module Federation capabilities in WebPack 5.

We will be making PRs to `jupyterlab_server` and `jupyterlab` once this work is stable.

See https://github.com/jupyterlab/jupyterlab/issues/7468 for full background and discussion.

Prereqs: `python 3.5+` and `nodejs`

To build:

```
pip install setuptools pip --upgrade
pip install -v -e ".[test]"
jlpm && jlpm run build
```

To run:

```
python main.py
```
