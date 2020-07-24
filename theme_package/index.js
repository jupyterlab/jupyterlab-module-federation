// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
import { IThemeManager } from '@jupyterlab/apputils';
/**
 * A plugin for the Jupyter Dark Theme.
 */
const plugin = {
    id: '@jupyterlab/example-federated-theme:plugin',
    requires: [IThemeManager],
    activate: (app, manager) => {
        const style = '@jupyterlab/example-federated-theme/index.css';
        manager.register({
            name: 'JupyterLab Dark',
            isLight: false,
            themeScrollbars: true,
            load: () => manager.loadCSS(style),
            unload: () => Promise.resolve(undefined)
        });
    },
    autoStart: true
};
export default plugin;
//# sourceMappingURL=index.js.map
