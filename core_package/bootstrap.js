// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// This is all the data needed to load and activate plugins. This should be
// gathered by the server and put onto the initial page template.
const PLUGIN_DATA = JSON.parse(
  document.getElementById('jupyterlab-plugin-data').textContent
);

import { PageConfig } from '@jupyterlab/coreutils';

// This must be after the public path is set.
// This cannot be extracted because the public path is dynamic.
require('./build/imports.css');

function loadScript(url) {
  return new Promise((resolve, reject) => {
    const newScript = document.createElement('script');
    newScript.onerror = reject;
    newScript.onload = resolve;
    newScript.async = true;
    document.head.appendChild(newScript);
    newScript.src = url;
  });
}

async function loadComponent(url, scope, module) {
  await loadScript(url);

  // From MIT-licensed https://github.com/module-federation/module-federation-examples/blob/af043acd6be1718ee195b2511adf6011fba4233c/advanced-api/dynamic-remotes/app1/src/App.js#L6-L12
  await __webpack_init_sharing__('default');
  const container = window._JUPYTERLAB[scope];
  // Initialize the container, it may provide shared modules and may need ours
  await container.init(__webpack_share_scopes__.default);

  const factory = await window._JUPYTERLAB[scope].get(module);
  const Module = factory();
  return Module;
}

window.addEventListener('load', async function() {
  const JupyterLab = require('@jupyterlab/application').JupyterLab;

  const pluginPromises = PLUGIN_DATA.map(data =>
    loadComponent(
      `${PageConfig.getBaseUrl()}/${data.path}`,
      data.name,
      data.module
    )
  );
  const plugins = await Promise.all(pluginPromises);

  // TODO: add logic from dev_mode/index.js for templating
  // and handling of deferred/disabled plugins
  const mods = [
    require('@jupyterlab/application-extension'),
    require('@jupyterlab/apputils-extension'),
    require('@jupyterlab/celltags-extension'),
    require('@jupyterlab/codemirror-extension'),
    require('@jupyterlab/completer-extension'),
    require('@jupyterlab/console-extension'),
    require('@jupyterlab/csvviewer-extension'),
    require('@jupyterlab/docmanager-extension'),
    require('@jupyterlab/documentsearch-extension'),
    require('@jupyterlab/extensionmanager-extension'),
    require('@jupyterlab/filebrowser-extension'),
    require('@jupyterlab/fileeditor-extension'),
    require('@jupyterlab/help-extension'),
    require('@jupyterlab/htmlviewer-extension'),
    require('@jupyterlab/hub-extension'),
    require('@jupyterlab/imageviewer-extension'),
    require('@jupyterlab/inspector-extension'),
    require('@jupyterlab/launcher-extension'),
    require('@jupyterlab/logconsole-extension'),
    require('@jupyterlab/mainmenu-extension'),
    require('@jupyterlab/markdownviewer-extension'),
    require('@jupyterlab/mathjax2-extension'),
    require('@jupyterlab/notebook-extension'),
    require('@jupyterlab/rendermime-extension'),
    require('@jupyterlab/running-extension'),
    require('@jupyterlab/settingeditor-extension'),
    require('@jupyterlab/shortcuts-extension'),
    require('@jupyterlab/statusbar-extension'),
    require('@jupyterlab/tabmanager-extension'),
    require('@jupyterlab/terminal-extension'),
    require('@jupyterlab/theme-dark-extension'),
    require('@jupyterlab/theme-light-extension'),
    require('@jupyterlab/toc-extension'),
    require('@jupyterlab/tooltip-extension'),
    require('@jupyterlab/ui-components-extension'),
    require('@jupyterlab/vdom-extension'),
    ...plugins
  ];

  const mimeExtensions = [
    require('@jupyterlab/javascript-extension'),
    require('@jupyterlab/json-extension'),
    require('@jupyterlab/pdf-extension'),
    require('@jupyterlab/vega5-extension')
  ];
  const lab = new JupyterLab({
    mimeExtensions
  });
  lab.registerPluginModules(mods);
  /* eslint-disable no-console */
  console.log('Starting app');
  await lab.start();
  console.log('App started, waiting for restore');
  await lab.restored;
  console.log('Example started!');
});

