# jupyterlab-module-federation

This repository is a temporary playground for implementing a new JupyterLab extension
system that utilizes the Module Federation capabilities in WebPack 5.

We will be making PRs to `jupyterlab_server` and `jupyterlab` once this work is stable.

See https://github.com/jupyterlab/jupyterlab/issues/7468 for full background and discussion.

## Installation

Prereqs: `python 3.5+` and `nodejs`

To build:

```
bash install.sh
```

To run:

```
python main.py
```

## Goals
- Users should be able to install and use extensions without requiring `node` or a build step
- Extension authors should be able to easily build and distribute extensions
- The existing capabilities of bundling extensions should still work
- Administrators should regain the ability to set global configuration and packages where possible
- Dynamic extensions should layer on top of existing extensions similar to how  `pip install --user` works
- Extensions should be discoverable

## Implementation
- We add a node script that extension authors use to build extension bundles - `@jupyterlab/buildutils -> build-labextension`
  - The script produces a set of static assets that are shipped along with a package (notionally on `pip`/`conda`)
  - The assets include a module federation `remoteEntry.js`, generated bundles, and some other files that we use
     - `package.orig.json` is the original `package.json` file that we use to gather metadata about the package
     - `build_log.json` has all of the webpack options used to build the extension, for debugging purposes
     - we use the existing `@jupyterlab/buildutils -> build` to generate the `imports.css`, `schemas` and `themes` file structure
- We add a schema for the valid `jupyterlab` metadata for an extension's `package.json` describing the available options
- We add a `labextensions` handler in `jupyterlab_server` that loads static assets from `labextensions` paths, following a similar logic to how `nbextensions` are discovered and loaded from disk
- We augment the `settings` and `themes` handlers in `jupyterlab_server` to load from the new `labextensions` locations, favoring the dynamic extension locations over the bundled ones
- We add a `labextension develop` command used to install an in-development extension into JupyterLab.  The default behavior is to create a symlink in the `sys-prefix/share/jupyter/labextensions/package-name` to the static directory of the extension
- We provide a `cookiecutter` that handles all of the scaffolding for an extension author, including the shipping of `data_files` so that when the user installs the package, the static assets end up in `share/jupyter/labextensions`
- We handle disabling of lab extensions using a trait on the `LabApp` class, so it can be set by admins and overridden by users.  Extensions are automatically enabled when installed, and must be explicitly disabled.  The disabled config can consist of a package name or a plugin regex pattern
- Extensions can provide `disabled` metadata that can be used to replace an entire extension or individual plugins
- `page_config` and `overrides` are also handled with traits so that admins can provide defaults and users can provide overrides
- We will update the `extension-manager` to target metadata on `pypi`/`conda` and consume those packages.

## Tools
- `build-labextension` node command line tool
- `jupyter labextension develop` python command line tool
- `cookiecutter` for extension authors

## Workflow for extension authors
- Use the `cookiecutter` to create the extension
- Run `jupyter labextension develop` to create the symlink
- Run `npm run watch` (included in the `cookiecutter`)
- Run `jupyter lab`
- Make changes to source
- Refresh the application page
- When finished, publish the package to `pypi`/`conda`

