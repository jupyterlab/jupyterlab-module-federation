## md_package

A federated markdown package

## Prequisites
- JupyterLab 3+
- node 12+

## Installation
- `pip install -e . && python ../labextensions.py develop .`

Notes:
- Assets are built into `md_package/static` so that the package is self-contained.  They are also shipped in `data_files` so the package is automatically installed as
a lab extension.
- Need to use the script from from `@jupyterlab/buildutils` when available
- Need to use `jupyter labextension develop` when available
- `pip install .` is broken - complains about `tsserver`
