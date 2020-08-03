## md_package

A federated markdown package

## Prequisites
- JupyterLab 3+
- node 12+

## Installation
- `pip install -e . && python ../labextensions.py develop .`

## Develop
- Run `jlpm run watch:all` to watch the source and build to static.


## Notes
- Assets are built into `md_package/static` so that the package is self-contained.  They are also shipped in `data_files` so the package is automatically installed as
a lab extension.
- Need to use the script from from `@jupyterlab/buildutils` when available
- Need to use `jupyter labextension develop` when available
- `pip install .` is broken - complains about `tsserver`
- Since `symlink=True` by default, there is no need to do anything special on the JupyterLab side,
just refresh the page when the extension assets update
