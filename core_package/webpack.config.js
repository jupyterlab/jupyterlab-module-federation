// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
const data = require('./package.json');
const Build = require('@jupyterlab/buildutils').Build;
const webpack = require('webpack');
const { merge } = require('webpack-merge');
const baseConfig = require('../webpack.config.base');
const { ModuleFederationPlugin } = webpack.container;
const path = require('path');

const names = Object.keys(data.dependencies).filter(function(name) {
  const packageData = require(name + '/package.json');
  return packageData.jupyterlab !== undefined;
});

const extras = Build.ensureAssets({
  packageNames: names,
  output: './build'
});

// TODO: make options configurable

const singletons = {};

data.jupyterlab.singletonPackages.forEach(element => {
  singletons[element] = { singleton: true }
});

module.exports = [
  merge(baseConfig, {
    entry: './index.js',
    output: {
      path: path.resolve(__dirname, 'build'),
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
