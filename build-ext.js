#!/usr/bin/env node
/* -----------------------------------------------------------------------------
| Copyright (c) Jupyter Development Team.
| Distributed under the terms of the Modified BSD License.
|----------------------------------------------------------------------------*/

// Build an extension

// Inputs:
// Path to extension (required)
// Dev vs prod (dev is default)
// Output path (defaults to <extension>/build)

// Outputs
// Webpack build assets

const commander = require('commander');
const path = require('path');
const run = require('@jupyterlab/buildutils').run;


commander
    .description('Build an extension')
    .usage('[options] <path>')
    .option('--prod', 'build in prod mode (default is dev)')
    .option('--output <path>', 'Output path (default is `<path-to-package>/build`')
    .action(
        async (cmd) => {
            let node_env = 'development';
            if (cmd.prod) {
                node_env = 'production';
            }
            const packagePath = path.resolve(cmd.args[0]);
            const output = cmd.output || path.join(packagePath, 'build');

            let cmdText = `npm run build:ext`;
            run(cmdText, { env: { ...process.env, OUTPUT_PATH: output, PACKAGE_PATH: packagePath, NODE_ENV: node_env } });
        }
    );

commander.parse(process.argv);

// If no arguments supplied
if (!process.argv.slice(2).length) {
    commander.outputHelp();
    process.exit(1);
}
