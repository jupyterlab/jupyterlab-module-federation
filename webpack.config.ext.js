// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

const Build = require('@jupyterlab/buildutils').Build;
const webpack = require('webpack');
const { merge } = require('webpack-merge');
const baseConfig = require('./webpack.config.base');
const { ModuleFederationPlugin } = webpack.container;
const path = require('path');
const fs = require('fs');
const Ajv = require('ajv');


const packagePath = process.env.PACKAGE_PATH;
const nodeEnv = process.env.NODE_ENV;

if (nodeEnv === 'production') {
  options.mode = 'production'
}

const data = require(path.join(packagePath, '/package.json'));

const ajv = new Ajv({ useDefaults: true });
const validate = ajv.compile(require('./metadata_schema.json'));
var valid = validate(data.jupyterlab || {});
if (!valid) {
  console.error(validate.errors);
  process.exit(1);
}

let outputPath = data.jupyterlab['outputDir'];
outputPath = path.join(packagePath, outputPath);

// Handle the extension entry point and the lib entry point, if different
let extEntry = data.jupyterlab.extension || data.jupyterlab.mimeExtension;
const index = require.resolve(packagePath);
const exposes = {
  './index': index,
  './extension': index
}

if (extEntry !== true) {
  exposes['./extension'] = path.join(packagePath, extEntry);
}

const coreData = require('./core_package/package.json');

const shared = {};

// Start with core dependencies.
Object.keys(coreData.dependencies).forEach((element) => {
  shared[element] = { requiredVersion: coreData.dependencies[element] };
  });

// Add package dependencies.
Object.keys(data.dependencies).forEach((element) => {
  if (!shared[element]) {
    shared[element] = {};
}
  shared[element].requiredVersion = data.dependencies[element];
});

// Remove non-shared.
(data.jupyterlab.nonSharedPackages || []).forEach((element) => {
  delete shared[element];
});

// Start with core singletons.
coreData.jupyterlab.singletonPackages.forEach((element) => {
  if (!shared[element]) {
    shared[element] = {};
}
  shared[element].import = false;
  shared[element].singleton = true;
});

// Add package singletons.
(data.jupyterlab.singletonPackages || []).forEach((element) => {
  if (!shared[element]) {
    shared[element] = {};
  }
  shared[element].import = false;
});

// Remove non-singletons.
(data.jupyterlab.nonSingletonPackages || []).forEach((element) => {
  if (!shared[element]) {
    shared[element] = {};
}
  shared[element].singleton = false;
});

// Ensure a clean output directory.
fs.rmdirSync(outputPath, { recursive: true });
fs.mkdirSync(outputPath, { recursive: true });

const extras = Build.ensureAssets({
  packageNames: [data.name],
  output: outputPath
});

// Make a bootstrap entrypoint
const entryPoint = path.join(outputPath, 'bootstrap.js');
const bootstrap = 'import("' + exposes['./extension'] + '");'
fs.writeFileSync(entryPoint, bootstrap);

module.exports = [
  merge(baseConfig, {
    entry: entryPoint,
    output: {
      filename: 'extension.js',
      path: outputPath,
      publicPath: `example/labextensions/${data.name}/`,
    },
    plugins: [
      new ModuleFederationPlugin({
        name: data.name,
        library: {
          type: 'var',
          name: ['_JUPYTERLAB', data.name]
        },
        filename: 'remoteEntry.js',
        exposes,
        shared,
      })
    ]
  })
].concat(extras);

const logPath = path.join(outputPath, 'build_log.json');
fs.writeFileSync(logPath, JSON.stringify(module.exports, null, '  '));
