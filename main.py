# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from jupyter_core.paths import jupyter_path
from jupyterlab_server import LabServerApp, LabConfig
from jupyterlab_server.server import FileFindHandler, APIHandler

from notebook.utils import url_path_join as ujoin, url_escape
import json
import os
from traitlets import Unicode, List

from tornado.web import StaticFileHandler

HERE = os.path.abspath(os.path.dirname(__file__))

# Turn off the Jupyter configuration system so configuration files on disk do
# not affect this app. This helps this app to truly be standalone.
os.environ["JUPYTER_NO_CONFIG"]="1"

with open(os.path.join(HERE, 'package.json')) as fid:
    version = json.load(fid)['version']


class SettingHandler(APIHandler):

    def get(self, schema_name=""):
        path = os.path.join(HERE, 'node_modules/@jupyterlab/markdownviewer-extension/schema/plugin.json')

        with open(path) as fid:
            schema = fid.read()

        # copy-pasta of typical response for now.
        result = {"id":"@jupyterlab/markdownviewer-extension:plugin","raw":"{}","schema":{"jupyter.lab.setting-icon":"ui-components:markdown","jupyter.lab.setting-icon-label":"Markdown Viewer","title":"Markdown Viewer","description":"Markdown viewer settings.","definitions":{"fontFamily":{"type":["string","null"]},"fontSize":{"type":["integer","null"],"minimum":1,"maximum":100},"lineHeight":{"type":["number","null"]},"lineWidth":{"type":["number","null"]},"hideFrontMatter":{"type":"boolean"},"renderTimeout":{"type":"number"}},"properties":{"fontFamily":{"title":"Font Family","description":"The font family used to render markdown.\nIf `null`, value from current theme is used.","$ref":"#/definitions/fontFamily","default":None},"fontSize":{"title":"Font Size","description":"The size in pixel of the font used to render markdown.\nIf `null`, value from current theme is used.","$ref":"#/definitions/fontSize","default":None},"lineHeight":{"title":"Line Height","description":"The line height used to render markdown.\nIf `null`, value from current theme is used.","$ref":"#/definitions/lineHeight","default":None},"lineWidth":{"title":"Line Width","description":"The text line width expressed in CSS ch units.\nIf `null`, lines fit the viewport width.","$ref":"#/definitions/lineWidth","default":None},"hideFrontMatter":{"title":"Hide Front Matter","description":"Whether to hide YAML front matter.\nThe YAML front matter must be placed at the top of the document,\nstarted by a line of three dashes (---) and ended by a line of\nthree dashes (---) or three points (...).","$ref":"#/definitions/hideFrontMatter","default":True},"renderTimeout":{"title":"Render Timeout","description":"The render timeout in milliseconds.","$ref":"#/definitions/renderTimeout","default":1000}},"additionalProperties":False,"type":"object"},"settings":{},"version":"2.2.0"}

        return self.finish(result)


class ExampleApp(LabServerApp):
    base_url = '/foo'
    default_url = Unicode('/example',
                          help='The default URL to redirect to from `/`')

    extra_labextensions_path = List(Unicode(), config=True,
        help="""extra paths to look for Javascript notebook extensions"""
    )

    lab_config = LabConfig(
        app_name = 'JupyterLab Example Federated App',
        app_settings_dir = os.path.join(HERE, 'build', 'application_settings'),
        app_version = version,
        app_url = '/example',
        schemas_dir = os.path.join(HERE, 'core_package', 'build', 'schemas'),
        static_dir = os.path.join(HERE, 'core_package', 'build'),
        templates_dir = os.path.join(HERE, 'templates'),
        themes_dir = os.path.join(HERE, 'core_package', 'build', 'themes'),
        user_settings_dir = os.path.join(HERE, 'core_package', 'build', 'user_settings'),
        workspaces_dir = os.path.join(HERE, 'core_package', 'build', 'workspaces'),
    )

    def init_webapp(self):
        super().init_webapp()

        # Handle labextension assets
        web_app = self.web_app
        base_url = web_app.settings['base_url']

        # Temporary addition for testing
        self.extra_labextensions_path += [os.path.join(HERE, 'labextensions')]

        labextensions_path = self.extra_labextensions_path + jupyter_path('labextensions')
        labextensions_url = ujoin(base_url, "example", r"labextensions/(.*)")
        web_app.add_handlers('.*$', [
            (labextensions_url, FileFindHandler, {
                'path': labextensions_path,
                'no_cache_paths': ['/'], # don't cache anything in labextensions
            })])

        ## Handle the specific setting
        static_path = ujoin(base_url, 'example', 'api', 'settings', '@jupyterlab', '(.*)')
        web_app.add_handlers('.*$', [(static_path, SettingHandler, {})])


    def start(self):
        settings = self.web_app.settings

        # By default, make terminals available.
        settings.setdefault('terminals_available', True)

        super().start()

if __name__ == '__main__':
    ExampleApp.launch_instance()
