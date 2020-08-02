# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from jupyter_core.paths import jupyter_path
from jupyterlab_server import LabServerApp, LabConfig
from jupyterlab_server.server import FileFindHandler, APIHandler

from notebook.utils import url_path_join as ujoin, url_escape
import json
import os
from traitlets import Unicode, List, Bool

from tornado.web import StaticFileHandler

from settings_handler import SettingsHandler
from themes_handler import ThemesHandler

HERE = os.path.abspath(os.path.dirname(__file__))

# Turn off the Jupyter configuration system so configuration files on disk do
# not affect this app. This helps this app to truly be standalone.
os.environ["JUPYTER_NO_CONFIG"]="1"

with open(os.path.join(HERE, 'package.json')) as fid:
    version = json.load(fid)['version']


class ExampleApp(LabServerApp):
    base_url = '/foo'
    default_url = Unicode('/example',
                          help='The default URL to redirect to from `/`')

    extra_labextensions_path = List(Unicode(), config=True,
        help="""extra paths to look for Javascript notebook extensions"""
    )

    browser_test = Bool(False, config=True)

    lab_config = LabConfig(
        app_name = 'JupyterLab Federated App',
        app_settings_dir = os.path.join(HERE, 'build', 'application_settings'),
        app_version = version,
        app_url = '/example',
        schemas_dir = os.path.join(HERE, 'core_package', 'static', 'schemas'),
        static_dir = os.path.join(HERE, 'core_package', 'static'),
        templates_dir = os.path.join(HERE, 'templates'),
        themes_dir = os.path.join(HERE, 'core_package', 'static', 'themes'),
        user_settings_dir = os.path.join(HERE, 'core_package', 'static', 'user_settings'),
        workspaces_dir = os.path.join(HERE, 'core_package', 'static', 'workspaces'),
    )

    def init_webapp(self):
        super().init_webapp()

        # Handle labextension assets
        web_app = self.web_app
        base_url = web_app.settings['base_url']
        page_config = web_app.settings.get('page_config_data', {})
        web_app.settings['page_config_data'] = page_config

        if self.browser_test:
            page_config['browserTest'] = True

        handlers = []

        labextensions_path = self.extra_labextensions_path + jupyter_path('labextensions')
        labextensions_url = ujoin(base_url, "example", r"labextensions/(.*)")
        handlers.append(
            (labextensions_url, FileFindHandler, {
                'path': labextensions_path,
                'no_cache_paths': ['/'], # don't cache anything in labextensions
            }))

        # Handle requests for the list of settings. Make slash optional.
        settings_path = ujoin(base_url, 'example', 'api', 'settings')
        settings_config = {
            'app_settings_dir': self.lab_config.app_settings_dir,
            'schemas_dir': self.lab_config.schemas_dir,
            'settings_dir': self.lab_config.user_settings_dir,
            'labextensions_path': labextensions_path
        }

        handlers.append((ujoin(settings_path, '?'), SettingsHandler, settings_config))

        # Handle requests for an individual set of settings.
        setting_path = ujoin(
            settings_path, '(?P<schema_name>.+)')
        handlers.append((setting_path, SettingsHandler, settings_config))

        # Handle requests for themes
        themes_path = ujoin(base_url, 'example', 'api', 'themes', '(.*)')
        handlers.append((
            themes_path,
            ThemesHandler,
            {
                'themes_url': themes_path,
                'path': self.lab_config.themes_dir,
                'labextensions_path': labextensions_path,
                'no_cache_paths': ['/']
            }
        ))

        web_app.add_handlers('.*$', handlers)

    def start(self):
        settings = self.web_app.settings

        # By default, make terminals available.
        settings.setdefault('terminals_available', True)

        super().start()

if __name__ == '__main__':
    ExampleApp.launch_instance()
