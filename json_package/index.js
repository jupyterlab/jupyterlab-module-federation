// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
import { Printing } from '@jupyterlab/apputils';
import { Widget } from '@lumino/widgets';
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { Component } from './component';
/**
 * The CSS class to add to the JSON Widget.
 */
const CSS_CLASS = 'jp-RenderedJSON';
/**
 * The MIME type for JSON.
 */
export const MIME_TYPE = 'application/json';
/**
 * A renderer for JSON data.
 */
export class RenderedJSON extends Widget {
    /**
     * Create a new widget for rendering JSON.
     */
    constructor(options) {
        super();
        this.addClass(CSS_CLASS);
        this.addClass('CodeMirror');
        this.addClass('cm-s-jupyter');
        this._mimeType = options.mimeType;
    }
    [Printing.symbol]() {
        return () => Printing.printWidget(this);
    }
    /**
     * Render JSON into this widget's node.
     */
    renderModel(model) {
        const data = (model.data[this._mimeType] || {});
        const metadata = (model.metadata[this._mimeType] || {});
        return new Promise((resolve, reject) => {
            ReactDOM.render(React.createElement(Component, { data: data, metadata: metadata }), this.node, () => {
                resolve();
            });
        });
    }
    /**
     * Called before the widget is detached from the DOM.
     */
    onBeforeDetach(msg) {
        // Unmount the component so it can tear down.
        ReactDOM.unmountComponentAtNode(this.node);
    }
}
/**
 * A mime renderer factory for JSON data.
 */
export const rendererFactory = {
    safe: true,
    mimeTypes: [MIME_TYPE],
    createRenderer: options => new RenderedJSON(options)
};
const extensions = [
    {
        id: '@jupyterlab/json-extension-federated:factory',
        rendererFactory,
        rank: 0,
        dataType: 'json',
        documentWidgetFactoryOptions: {
            name: 'JSON (FEDERATED)',
            primaryFileType: 'json',
            fileTypes: ['json', 'notebook', 'geojson']
        }
    }
];
export default extensions;
//# sourceMappingURL=index.js.map
