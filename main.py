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

from commands import get_app_info

HERE = os.path.abspath(os.path.dirname(__file__))

# Turn off the Jupyter configuration system so configuration files on disk do
# not affect this app. This helps this app to truly be standalone.
os.environ["JUPYTER_NO_CONFIG"]="1"

with open(os.path.join(HERE, 'package.json')) as fid:
    version = json.load(fid)['version']


class ExampleApp(LabServerApp):
    name = "lab"
    app_name = "JupyterLab"
    load_other_extensions = True
    
    default_url = Unicode('/lab',
                          help='The default URL to redirect to from `/`')
    browser_test = Bool(False, config=True)

    lab_config = LabConfig(
        app_name = 'JupyterLab Federated App',
        app_settings_dir = os.path.join(HERE, 'build', 'application_settings'),
        app_version = version,
        app_url = '/lab',
        schemas_dir = os.path.join(HERE, 'core_package', 'static', 'schemas'),
        static_dir = os.path.join(HERE, 'core_package', 'static'),
        templates_dir = os.path.join(HERE, 'templates'),
        themes_dir = os.path.join(HERE, 'core_package', 'static', 'themes'),
        user_settings_dir = os.path.join(HERE, 'core_package', 'static', 'user_settings'),
        workspaces_dir = os.path.join(HERE, 'core_package', 'static', 'workspaces'),
    )

    def initialize_templates(self):
        import pdb; pdb.set_trace()
        self.static_paths = [self.lab_config.static_dir]
        self.template_paths = [self.lab_config.templates_dir]

    def initialize_handlers(self):
        # Handle labextension assets
        import pdb; pdb.set_trace()
        web_app = self.serverapp.web_app
        base_url = web_app.settings['base_url']
        page_config = web_app.settings.get('page_config_data', {})
        web_app.settings['page_config_data'] = page_config

        # By default, make terminals available.
        web_app.settings.setdefault('terminals_available', True)

        if self.browser_test:
            page_config['browserTest'] = True

        info = get_app_info()
        dynamic_extensions = page_config['dynamic_extensions'] = []
        dynamic_mime_extension = page_config['dynamic_mime_extensions'] = []
        for (ext, ext_data) in info['dynamic_exts'].items():
            name = ext_data['name']
            path = "lab/extensions/%s/remoteEntry.js" % name
            module = "./extension"
            load_data = dict(name=name, path=path, module=module)
            if ext_data['jupyterlab'].get('extension'):
                dynamic_extensions.append(load_data)
            else:
                dynamic_mime_extension.append(load_data)

if __name__ == '__main__':
    import pdb; pdb.set_trace()
    ExampleApp.launch_instance()
