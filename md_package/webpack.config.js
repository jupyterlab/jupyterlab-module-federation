// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// TODO: this path should be configurable in final script
const data = require('./package.json');
const Build = require('@jupyterlab/buildutils').Build;
const webpack = require('webpack');
const { ModuleFederationPlugin } = webpack.container;
const path = require('path');


const extras = Build.ensureAssets({
  packageNames: [data.name],
  output: './build'
});

const rules = [
  { test: /\.css$/, use: ['style-loader', 'css-loader'] },
  { test: /\.html$/, use: 'file-loader' },
  { test: /\.md$/, use: 'raw-loader' },
  { test: /\.(jpg|png|gif)$/, use: 'file-loader' },
  { test: /\.js.map$/, use: 'file-loader' },
  {
    test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/,
    use: 'url-loader?limit=10000&mimetype=application/font-woff'
  },
  {
    test: /\.woff(\?v=\d+\.\d+\.\d+)?$/,
    use: 'url-loader?limit=10000&mimetype=application/font-woff'
  },
  {
    test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/,
    use: 'url-loader?limit=10000&mimetype=application/octet-stream'
  },
  { test: /\.eot(\?v=\d+\.\d+\.\d+)?$/, use: 'file-loader' },
  {
    // In .css files, svg is loaded as a data URI.
    test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
    issuer: /\.css$/,
    use: {
      loader: 'svg-url-loader',
      options: { encoding: 'none', limit: 10000 }
    }
  },
  {
    // In .ts and .tsx files (both of which compile to .js), svg files
    // must be loaded as a raw string instead of data URIs.
    test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
    issuer: /\.js$/,
    use: {
      loader: 'raw-loader'
    }
  }
];

// TODO: this should be configurable
const options = {
  devtool: 'source-map',
  bail: true,
  mode: 'development'
};

// TODO: update handling of this data - passed in as a path to this script?
const coreData = require('../core_package/package.json');

// Start with core singletons.
const singletons = {};
coreData.jupyterlab.singletonPackages.forEach(element => {
  singletons[element] = { singleton: true }
});

// Add package singletons.
if (data.jupyterlab.singletonPackages) {
  data.jupyterlab.singletonPackages.forEach(element => {
    singletons[element] = { singleton: true }
  });
}

// Remove non-singletons.
if (data.jupyterlab.nonSingletonPackages) {
  data.jupyterlab.nonSingletonPackages.forEach(element => {
    delete singletons[element];
  });
}

// Start with core shared.
const shared = coreData.dependencies;

// Add package shared.
Object.keys(data.dependencies).forEach(element => {
  shared[element] = data.dependencies[element];
});

// Remove non-shared.
if (data.jupyterlab.nonSharedPackages) {
  data.jupyterlab.nonSharedPackages.forEach(element => {
    delete shared[element];
  })
}

module.exports = [
  {
    // TODO: this should be based on jupyterlab metadata (and could be more than one type?)
    entry: './index.js',
    output: {
      filename: 'extension.js',
      path: path.resolve(__dirname, 'build'),
      publicPath: 'example/labextensions/' + data.name + '/'
    },
    ...options,
    module: { rules },
    resolve: { alias: { "url": false, "buffer": false } },
    plugins: [
      new ModuleFederationPlugin({
        name: data.name,
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', data.name]
        },
        filename: 'remoteEntry.js',
        exposes: {
          './index': './index.js'
        },
        shared: {
          ...shared,
          ...singletons
        }
      }),
      new webpack.DefinePlugin({
        'process.env': '{}',
        process: {}
      })
    ]
  }
].concat(extras);
