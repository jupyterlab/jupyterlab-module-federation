# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from jupyterlab_server import LabServerApp, LabConfig
from jupyterlab_server.server import FileFindHandler, APIHandler
from notebook.utils import url_path_join as ujoin, url_escape
import json
import os
from traitlets import Unicode

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
            data = fid.read()
        return self.finish(data)
        
    
class ExtensionHandler(FileFindHandler):

    def get(self, path):
        extname, _, rest = path.partition('/')
        dirname = 'md_package' if extname == 'example-federated-md' else 'middle_package'
        path = os.path.join(dirname, 'build', rest)
        return super().get(path)


class ExampleApp(LabServerApp):
    base_url = '/foo'
    default_url = Unicode('/example',
                          help='The default URL to redirect to from `/`')

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

        # Handle md ext assets
        web_app = self.web_app
        base_url = web_app.settings['base_url']

        static_path = ujoin(base_url, 'example', 'labextensions', '@jupyterlab', '(.*)')
        web_app.add_handlers('.*$', [(static_path, ExtensionHandler, { 'path': HERE })])

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
