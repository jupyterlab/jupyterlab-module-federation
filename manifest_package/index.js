// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
/**
 * A plugin for the Jupyter Dark Theme.
 */

import manifest from '../pluginManifest.json';
import _ from "lodash";

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

const plugin = {
    id: '@jupyterlab/example-federated-manifest:plugin',
    requires: [],
    activate: async (app, manager) => {
        console.log("Manifest plugin activated!");
        console.log("Trying to load another packages bundle" + _.repeat(".", 5));

        const anotherBundle = manifest.plugins.another;

        const { default: foo } = await loadComponent(
            anotherBundle.url,
            anotherBundle.name,
            anotherBundle.path
        );
        foo();
    },
    autoStart: true
};
export default plugin;
//# sourceMappingURL=index.js.map
