// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

const Build = require('@jupyterlab/buildutils').Build;
const webpack = require('webpack');
const { ModuleFederationPlugin } = webpack.container;
const path = require('path');
const fs = require('fs');

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

const options = {
  devtool: 'source-map',
  bail: true,
  mode: 'development'
};

const packagePath = process.env.PACKAGE_PATH;
const outputPath = process.env.OUTPUT_PATH;
const nodeEnv = process.env.NODE_ENV;

if (nodeEnv === 'production') {
  options.mode = 'production'
}

const data = require(path.join(packagePath, '/package.json'));

const extras = Build.ensureAssets({
  packageNames: [data.name],
  output: outputPath
});

let entryPoint = data.jupyterlab.extension;
if (entryPoint === undefined) {
  entryPoint = data.jupyterlab.mimeExtension;
}

if (entryPoint === true) {
  if (entryPoint === true) {
    // Use require to get the entry point
    entryPoint = require.resolve(packagePath);
  } else {
    // Use the path to get the entry point
    entryPoint = path.join(packagePath, entryPoint);
  }
}

const coreData = require('./core_package/package.json');

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

// Ensure a clean output directory.
fs.rmdirSync(outputPath, { recursive: true });


module.exports = [
  {
    entry: entryPoint,
    output: {
      filename: 'extension.js',
      path: outputPath,
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
          './index': entryPoint
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

