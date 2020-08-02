// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
const data = require('./package.json');
const Build = require('@jupyterlab/buildutils').Build;
const webpack = require('webpack');
const { merge } = require('webpack-merge');
const baseConfig = require('../webpack.config.base');
const { ModuleFederationPlugin } = webpack.container;
const fs = require('fs-extra');
const path = require('path');
const Handlebars = require('handlebars');

const names = Object.keys(data.dependencies).filter(function(name) {
  const packageData = require(name + '/package.json');
  return packageData.jupyterlab !== undefined;
});

const jlab = data.jupyterlab;

// Ensure a clear build directory.
const buildDir = path.resolve(jlab.buildDir);
if (fs.existsSync(buildDir)) {
  fs.removeSync(buildDir);
}
fs.ensureDirSync(buildDir);

const extras = Build.ensureAssets({
  packageNames: names,
  output: jlab.outputDir
});

// TODO: make options configurable

const singletons = {};

data.jupyterlab.singletonPackages.forEach(element => {
  singletons[element] = { singleton: true }
});

// Handle the extensions.
const extensions = jlab.extensions || {};
const mimeExtensions = jlab.mimeExtensions || {};
const externalExtensions = jlab.externalExtensions || {};
const packageNames = Object.keys(mimeExtensions).concat(
  Object.keys(extensions),
  Object.keys(externalExtensions)
);

// go throught each external extension
// add to mapping of extension and mime extensions, of package name
// to path of the extension.
for (const key in externalExtensions) {
  const {
    jupyterlab: { extension, mimeExtension }
  } = require(`${key}/package.json`);
  if (extension !== undefined) {
    extensions[key] = extension === true ? '' : extension;
  }
  if (mimeExtension !== undefined) {
    mimeExtensions[key] = mimeExtension === true ? '' : mimeExtension;
  }
}

// Create the entry point file.
const source = fs.readFileSync('index.js').toString();
const template = Handlebars.compile(source);
const extData = {
  jupyterlab_extensions: extensions,
  jupyterlab_mime_extensions: mimeExtensions
};
const result = template(extData);

fs.writeFileSync(path.join(buildDir, 'index.out.js'), result);

// Make a bootstrap entrypoint
const entryPoint = path.join(buildDir, 'bootstrap.js');
const bootstrap = 'import("./index.out.js");'
fs.writeFileSync(entryPoint, bootstrap);

module.exports = [
  merge(baseConfig, {
    entry: entryPoint,
    output: {
      path: path.resolve(jlab.outputDir),
      library: {
        type: 'var',
        name: ['_JUPYTERLAB', 'CORE_OUTPUT']
      },
      filename: 'bundle.js',
      // TODO: make this part of config so it can be different for other apps.
      publicPath: 'static/example/'
    },
    plugins: [
      new ModuleFederationPlugin({
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', 'CORE_LIBRARY_FEDERATION']
        },
        name: 'CORE_FEDERATION',
        shared: {
          ...data.dependencies,
          ...singletons
        }
      })
    ]
  })
].concat(extras);
