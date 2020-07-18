// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
const data = require('./package.json');
const Build = require('@jupyterlab/buildutils').Build;
const webpack = require('webpack');
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

// TODO: make this configurable
const options = {
  devtool: 'source-map',
  bail: true,
  mode: 'development'
};

const singletons = {};

data.jupyterlab.singletonPackages.forEach(element => {
  singletons[element] = { singleton: true }
});

module.exports = [
  {
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
    stats: 'verbose',
    ...options,
    module: { rules },
    resolve: { alias: { "url": false, "buffer": false } },
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
      }),
      new webpack.DefinePlugin({
        'process.env': '{}',
        process: {}
      })
    ]
  }
].concat(extras);
