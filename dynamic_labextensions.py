# coding: utf-8
"""Utilities for installing Javascript extensions for the notebook"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import os
import shutil
import sys
import tarfile
import zipfile
from os.path import basename, join as pjoin, normpath

from urllib.parse import urlparse
from urllib.request import urlretrieve
from jupyter_core.paths import (
    jupyter_data_dir, jupyter_config_path, jupyter_path,
    SYSTEM_JUPYTER_PATH, ENV_JUPYTER_PATH,
)
from jupyter_core.utils import ensure_dir_exists
from ipython_genutils.py3compat import string_types, cast_unicode_py2
from ipython_genutils.tempdir import TemporaryDirectory
from notebook.config_manager import BaseJSONConfigManager

from traitlets.utils.importstring import import_item

DEPRECATED_ARGUMENT = object()

__version__ = '0.1.0'


#------------------------------------------------------------------------------
# Public API
#------------------------------------------------------------------------------

def check_labextension(files, user=False, labextensions_dir=None, sys_prefix=False):
    """Check whether labextension files have been installed
    
    Returns True if all files are found, False if any are missing.

    Parameters
    ----------

    files : list(paths)
        a list of relative paths within labextensions.
    user : bool [default: False]
        Whether to check the user's .jupyter/labextensions directory.
        Otherwise check a system-wide install (e.g. /usr/local/share/jupyter/labextensions).
    labextensions_dir : str [optional]
        Specify absolute path of labextensions directory explicitly.
    sys_prefix : bool [default: False]
        Install into the sys.prefix, i.e. environment
    """
    labext = _get_labextension_dir(user=user, sys_prefix=sys_prefix, labextensions_dir=labextensions_dir)
    # make sure labextensions dir exists
    if not os.path.exists(labext):
        return False
    
    if isinstance(files, string_types):
        # one file given, turn it into a list
        files = [files]
    
    return all(os.path.exists(pjoin(labext, f)) for f in files)


def install_labextension(path, symlink=False, overwrite=False,
                        user=False, labextensions_dir=None,
                        destination=None, 
                        logger=None, sys_prefix=False
                        ):
    """Install a Javascript extension for the notebook
    
    Stages files and/or directories into the labextensions directory.
    By default, this compares modification time, and only stages files that need updating.
    If `overwrite` is specified, matching files are purged before proceeding.
    
    Parameters
    ----------
    
    path : path to file, directory, zip or tarball archive, or URL to install
        By default, the file will be installed with its base name, so '/path/to/foo'
        will install to 'labextensions/foo'. See the destination argument below to change this.
        Archives (zip or tarballs) will be extracted into the labextensions directory.
    user : bool [default: False]
        Whether to install to the user's labextensions directory.
        Otherwise do a system-wide install (e.g. /usr/local/share/jupyter/labextensions).
    overwrite : bool [default: False]
        If True, always install the files, regardless of what may already be installed.
    symlink : bool [default: False]
        If True, create a symlink in labextensions, rather than copying files.
        Windows support for symlinks requires a permission bit which only admin users
        have by default, so don't rely on it.
    labextensions_dir : str [optional]
        Specify absolute path of labextensions directory explicitly.
    destination : str [optional]
        name the labextension is installed to.  For example, if destination is 'foo', then
        the source file will be installed to 'labextensions/foo', regardless of the source name.
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    # the actual path to which we eventually installed
    full_dest = None

    labext = _get_labextension_dir(user=user, sys_prefix=sys_prefix, labextensions_dir=labextensions_dir)
    # make sure labextensions dir exists
    ensure_dir_exists(labext)

    
    if isinstance(path, (list, tuple)):
        raise TypeError("path must be a string pointing to a single extension to install; call this function multiple times to install multiple extensions")
    
    path = cast_unicode_py2(path)

    if not destination:
        destination = basename(normpath(path))
    destination = cast_unicode_py2(destination)
    full_dest = normpath(pjoin(labext, destination))
    if overwrite and os.path.lexists(full_dest):
        if logger:
            logger.info("Removing: %s" % full_dest)
        if os.path.isdir(full_dest) and not os.path.islink(full_dest):
            shutil.rmtree(full_dest)
        else:
            os.remove(full_dest)

    if symlink:
        path = os.path.abspath(path)
        if not os.path.exists(full_dest):
            if logger:
                logger.info("Symlinking: %s -> %s" % (full_dest, path))
            os.symlink(path, full_dest)
    elif os.path.isdir(path):
        path = pjoin(os.path.abspath(path), '') # end in path separator
        for parent, dirs, files in os.walk(path):
            dest_dir = pjoin(full_dest, parent[len(path):])
            if not os.path.exists(dest_dir):
                if logger:
                    logger.info("Making directory: %s" % dest_dir)
                os.makedirs(dest_dir)
            for file_name in files:
                src = pjoin(parent, file_name)
                dest_file = pjoin(dest_dir, file_name)
                _maybe_copy(src, dest_file, logger=logger)
    else:
        src = path
        _maybe_copy(src, full_dest, logger=logger)

    return full_dest


def develop_labextension(module, user=False, sys_prefix=False, overwrite=False, symlink=False, labextensions_dir=None, logger=None):
    """Install an labextension bundled in a Python package.

    Returns a list of installed/updated directories.

    See install_labextension for parameter information."""
    m, labexts = _get_labextension_metadata(module)
    base_path = os.path.split(m.__file__)[0]

    full_dests = []

    for labext in labexts:
        src = os.path.join(base_path, labext['src'])
        dest = labext['dest']

        if logger:
            logger.info("Installing %s -> %s" % (src, dest))
        full_dest = install_labextension(
            src, overwrite=overwrite, symlink=symlink,
            user=user, sys_prefix=sys_prefix, labextensions_dir=labextensions_dir,
            destination=dest, logger=logger
            )
        full_dests.append(full_dest)

    return full_dests


def uninstall_labextension(dest, require=None, user=False, sys_prefix=False, prefix=None, 
                          labextensions_dir=None, logger=None):
    """Uninstall a Javascript extension of the notebook
    
    Removes staged files and/or directories in the labextensions directory and 
    removes the extension from the frontend config.
    
    Parameters
    ----------
    
    dest : str
        path to file, directory, zip or tarball archive, or URL to install
        name the labextension is installed to.  For example, if destination is 'foo', then
        the source file will be installed to 'labextensions/foo', regardless of the source name.
        This cannot be specified if an archive is given as the source.
    require : str [optional]
        require.js path used to load the extension.
        If specified, frontend config loading extension will be removed.
    user : bool [default: False]
        Whether to install to the user's labextensions directory.
        Otherwise do a system-wide install (e.g. /usr/local/share/jupyter/labextensions).
    prefix : str [optional]
        Specify install prefix, if it should differ from default (e.g. /usr/local).
        Will install to ``<prefix>/share/jupyter/labextensions``
    labextensions_dir : str [optional]
        Specify absolute path of labextensions directory explicitly.
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    labext = _get_labextension_dir(user=user, sys_prefix=sys_prefix, prefix=prefix, labextensions_dir=labextensions_dir)
    dest = cast_unicode_py2(dest)
    full_dest = pjoin(labext, dest)
    if os.path.lexists(full_dest):
        if logger:
            logger.info("Removing: %s" % full_dest)
        if os.path.isdir(full_dest) and not os.path.islink(full_dest):
            shutil.rmtree(full_dest)
        else:
            os.remove(full_dest)
    
    # Look through all of the config sections making sure that the labextension
    # doesn't exist.
    config_dir = os.path.join(_get_config_dir(user=user, sys_prefix=sys_prefix), 'nbconfig')
    cm = BaseJSONConfigManager(config_dir=config_dir)
    if require:
        for section in NBCONFIG_SECTIONS:
            cm.update(section, {"load_extensions": {require: None}})


def _find_uninstall_labextension(filename, logger=None):
    """Remove labextension files from the first location they are found.

    Returns True if files were removed, False otherwise.
    """
    filename = cast_unicode_py2(filename)
    for labext in jupyter_path('labextensions'):
        path = pjoin(labext, filename)
        if os.path.lexists(path):
            if logger:
                logger.info("Removing: %s" % path)
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return True

    return False


def uninstall_labextension_python(module,
                        user=False, sys_prefix=False, prefix=None, labextensions_dir=None,
                        logger=None):
    """Uninstall an labextension bundled in a Python package.
    
    See parameters of `install_labextension_python`
    """
    m, labexts = _get_labextension_metadata(module)
    for labext in labexts:
        dest = labext['dest']
        require = labext['require']
        if logger:
            logger.info("Uninstalling {} {}".format(dest, require))
        uninstall_labextension(dest, require, user=user, sys_prefix=sys_prefix, 
            prefix=prefix, labextensions_dir=labextensions_dir, logger=logger)


def _set_labextension_state(section, require, state,
                           user=True, sys_prefix=False, logger=None):
    """Set whether the section's frontend should require the named labextension

    Returns True if the final state is the one requested.

    Parameters
    ----------
    section : string
        The section of the server to change, one of NBCONFIG_SECTIONS
    require : string
        An importable AMD module inside the labextensions static path
    state : bool
        The state in which to leave the extension
    user : bool [default: True]
        Whether to update the user's .jupyter/labextensions directory
    sys_prefix : bool [default: False]
        Whether to update the sys.prefix, i.e. environment. Will override
        `user`.
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    user = False if sys_prefix else user
    config_dir = os.path.join(
        _get_config_dir(user=user, sys_prefix=sys_prefix), 'nbconfig')
    cm = BaseJSONConfigManager(config_dir=config_dir)
    if logger:
        logger.info("{} {} extension {}...".format(
            "Enabling" if state else "Disabling",
            section,
            require
        ))
    cm.update(section, {"load_extensions": {require: state}})

    validate_labextension(require, logger=logger)

    return cm.get(section).get(require) == state


def _set_labextension_state_python(state, module, user, sys_prefix,
                                  logger=None):
    """Enable or disable some labextensions stored in a Python package

    Returns a list of whether the state was achieved (i.e. changed, or was
    already right)

    Parameters
    ----------

    state : Bool
        Whether the extensions should be enabled
    module : str
        Importable Python module exposing the
        magic-named `_jupyter_labextension_paths` function
    user : bool
        Whether to enable in the user's labextensions directory.
    sys_prefix : bool
        Enable/disable in the sys.prefix, i.e. environment
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    m, labexts = _get_labextension_metadata(module)
    return [_set_labextension_state(section=labext["section"],
                                   require=labext["require"],
                                   state=state,
                                   user=user, sys_prefix=sys_prefix,
                                   logger=logger)
            for labext in labexts]


def enable_labextension(section, require, user=True, sys_prefix=False,
                       logger=None):
    """Enable a named labextension

    Returns True if the final state is the one requested.

    Parameters
    ----------

    section : string
        The section of the server to change, one of NBCONFIG_SECTIONS
    require : string
        An importable AMD module inside the labextensions static path
    user : bool [default: True]
        Whether to enable in the user's labextensions directory.
    sys_prefix : bool [default: False]
        Whether to enable in the sys.prefix, i.e. environment. Will override
        `user`
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    return _set_labextension_state(section=section, require=require,
                                  state=True,
                                  user=user, sys_prefix=sys_prefix,
                                  logger=logger)


def disable_labextension(section, require, user=True, sys_prefix=False,
                        logger=None):
    """Disable a named labextension
    
    Returns True if the final state is the one requested.

    Parameters
    ----------

    section : string
        The section of the server to change, one of NBCONFIG_SECTIONS
    require : string
        An importable AMD module inside the labextensions static path
    user : bool [default: True]
        Whether to enable in the user's labextensions directory.
    sys_prefix : bool [default: False]
        Whether to enable in the sys.prefix, i.e. environment. Will override
        `user`.
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    return _set_labextension_state(section=section, require=require,
                                  state=False,
                                  user=user, sys_prefix=sys_prefix,
                                  logger=logger)


def _find_disable_labextension(section, require, logger=None):
    """Disable an labextension from the first config location where it is enabled.

    Returns True if it changed any config, False otherwise.
    """
    for config_dir in jupyter_config_path():
        cm = BaseJSONConfigManager(
            config_dir=os.path.join(config_dir, 'nbconfig'))
        d = cm.get(section)
        if d.get('load_extensions', {}).get(require, None):
            if logger:
                logger.info("Disabling %s extension in %s", require, config_dir)
            cm.update(section, {'load_extensions': {require: None}})
            return True

    return False


def enable_labextension_python(module, user=True, sys_prefix=False,
                              logger=None):
    """Enable some labextensions associated with a Python module.

    Returns a list of whether the state was achieved (i.e. changed, or was
    already right)

    Parameters
    ----------

    module : str
        Importable Python module exposing the
        magic-named `_jupyter_labextension_paths` function
    user : bool [default: True]
        Whether to enable in the user's labextensions directory.
    sys_prefix : bool [default: False]
        Whether to enable in the sys.prefix, i.e. environment. Will override
        `user`
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    return _set_labextension_state_python(True, module, user, sys_prefix,
                                         logger=logger)


def disable_labextension_python(module, user=True, sys_prefix=False,
                               logger=None):
    """Disable some labextensions associated with a Python module.
    
    Returns True if the final state is the one requested.

    Parameters
    ----------

    module : str
        Importable Python module exposing the
        magic-named `_jupyter_labextension_paths` function
    user : bool [default: True]
        Whether to enable in the user's labextensions directory.
    sys_prefix : bool [default: False]
        Whether to enable in the sys.prefix, i.e. environment
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    return _set_labextension_state_python(False, module, user, sys_prefix,
                                         logger=logger)


def validate_labextension(require, logger=None):
    """Validate a named labextension.

    Looks across all of the labextension directories.

    Returns a list of warnings.

    require : str
        require.js path used to load the extension
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    warnings = []
    infos = []

    js_exists = False
    for exts in jupyter_path('labextensions'):
        # Does the Javascript entrypoint actually exist on disk?
        js = u"{}.js".format(os.path.join(exts, *require.split("/")))
        js_exists = os.path.exists(js)
        if js_exists:
            break

    require_tmpl = u"        - require? {} {}"
    if js_exists:
        infos.append(require_tmpl.format(GREEN_OK, require))
    else:
        warnings.append(require_tmpl.format(RED_X, require))
    
    if logger:
        if warnings:
            logger.warning(u"      - Validating: problems found:")
            for msg in warnings:
                logger.warning(msg)
            for msg in infos:
                logger.info(msg)
        else:
            logger.info(u"      - Validating: {}".format(GREEN_OK))
    
    return warnings


def validate_labextension_python(spec, full_dest, logger=None):
    """Assess the health of an installed labextension

    Returns a list of warnings.

    Parameters
    ----------

    spec : dict
        A single entry of _jupyter_labextension_paths():
            [{
                'section': 'notebook',
                'src': 'mockextension',
                'dest': '_mockdestination',
                'require': '_mockdestination/index'
            }]
    full_dest : str
        The on-disk location of the installed labextension: this should end
        with `labextensions/<dest>`
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    infos = []
    warnings = []

    section = spec.get("section", None)
    if section in NBCONFIG_SECTIONS:
        infos.append(u"  {} section: {}".format(GREEN_OK, section))
    else:
        warnings.append(u"  {}  section: {}".format(RED_X, section))

    require = spec.get("require", None)
    if require is not None:
        require_path = os.path.join(
            full_dest[0:-len(spec["dest"])],
            u"{}.js".format(require))
        if os.path.exists(require_path):
            infos.append(u"  {} require: {}".format(GREEN_OK, require_path))
        else:
            warnings.append(u"  {}  require: {}".format(RED_X, require_path))

    if logger:
        if warnings:
            logger.warning("- Validating: problems found:")
            for msg in warnings:
                logger.warning(msg)
            for msg in infos:
                logger.info(msg)
            logger.warning(u"Full spec: {}".format(spec))
        else:
            logger.info(u"- Validating: {}".format(GREEN_OK))

    return warnings


#----------------------------------------------------------------------
# Applications
#----------------------------------------------------------------------

from notebook.extensions import (
    BaseExtensionApp, _get_config_dir, GREEN_ENABLED, RED_DISABLED, GREEN_OK, RED_X,
    ArgumentConflict, _base_aliases, _base_flags,
)
from traitlets import Bool, Unicode

flags = {}
flags.update(_base_flags)
flags.update({
    "overwrite" : ({
        "InstalllabextensionApp" : {
            "overwrite" : True,
        }}, "Force overwrite of existing files"
    ),
    "symlink" : ({
        "InstalllabextensionApp" : {
            "symlink" : True,
        }}, "Create symlink instead of copying files"
    ),
})

flags['s'] = flags['symlink']

aliases = {}
aliases.update(_base_aliases)
aliases.update({
    "prefix" : "InstalllabextensionApp.prefix",
    "labextensions" : "InstalllabextensionApp.labextensions_dir",
    "destination" : "InstalllabextensionApp.destination",
})

class InstalllabextensionApp(BaseExtensionApp):
    """Entry point for installing notebook extensions"""
    description = """Install Jupyter notebook extensions
    
    Usage
    
        jupyter labextension install path|url [--user|--sys-prefix]
    
    This copies a file or a folder into the Jupyter labextensions directory.
    If a URL is given, it will be downloaded.
    If an archive is given, it will be extracted into labextensions.
    If the requested files are already up to date, no action is taken
    unless --overwrite is specified.
    """
    
    examples = """
    jupyter labextension install /path/to/myextension
    """
    aliases = aliases
    flags = flags
    
    overwrite = Bool(False, config=True, help="Force overwrite of existing files")
    symlink = Bool(False, config=True, help="Create symlinks instead of copying files")

    prefix = Unicode('', config=True, help="Installation prefix")
    labextensions_dir = Unicode('', config=True,
           help="Full path to labextensions dir (probably use prefix or user)")
    destination = Unicode('', config=True, help="Destination for the copy or symlink")

    def _config_file_name_default(self):
        """The default config file name."""
        return 'jupyter_notebook_config'
    
    def install_labextensions(self):
        """Perform the installation of labextension(s)"""
        if len(self.extra_args)>1:
            raise ValueError("Only one labextension allowed at a time. "
                         "Call multiple times to install multiple extensions.")

        if self.python:
            install = install_labextension_python
            kwargs = {}
        else:
            install = install_labextension
            kwargs = {'destination': self.destination}
        
        full_dests = install(self.extra_args[0],
                             overwrite=self.overwrite,
                             symlink=self.symlink,
                             user=self.user,
                             sys_prefix=self.sys_prefix,
                             prefix=self.prefix,
                             labextensions_dir=self.labextensions_dir,
                             logger=self.log,
                             **kwargs
                            )

        if full_dests:
            self.log.info(
                u"\nTo initialize this labextension in the browser every time"
                " the notebook (or other app) loads:\n\n"
                "      jupyter labextension enable {}{}{}{}\n".format(
                    self.extra_args[0] if self.python else "<the entry point>",
                    " --user" if self.user else "",
                    " --py" if self.python else "",
                    " --sys-prefix" if self.sys_prefix else ""
                )
            )

    def start(self):
        """Perform the App's function as configured"""
        if not self.extra_args:
            sys.exit('Please specify an labextension to install')
        else:
            try:
                self.install_labextensions()
            except ArgumentConflict as e:
                sys.exit(str(e))


class UninstalllabextensionApp(BaseExtensionApp):
    """Entry point for uninstalling notebook extensions"""
    version = __version__
    description = """Uninstall Jupyter notebook extensions
    
    Usage
    
        jupyter labextension uninstall path/url path/url/entrypoint
        jupyter labextension uninstall --py pythonPackageName

    This uninstalls an labextension. By default, it uninstalls from the
    first directory on the search path where it finds the extension, but you can
    uninstall from a specific location using the --user, --sys-prefix or
    --system flags, or the --prefix option.

    If you specify the --require option, the named extension will be disabled,
    e.g.::

        jupyter labextension uninstall myext --require myext/main

    If you use the --py or --python flag, the name should be a Python module.
    It will uninstall labextensions listed in that module, but not the module
    itself (which you should uninstall using a package manager such as pip).
    """
    
    examples = """
    jupyter labextension uninstall dest/dir dest/dir/extensionjs
    jupyter labextension uninstall --py extensionPyPackage
    """
    
    aliases = {
        "prefix" : "UninstalllabextensionApp.prefix",
        "labextensions" : "UninstalllabextensionApp.labextensions_dir",
        "require": "UninstalllabextensionApp.require",
    }
    flags = BaseExtensionApp.flags.copy()
    flags['system'] = ({'UninstalllabextensionApp': {'system': True}},
        "Uninstall specifically from systemwide installation directory")
    
    prefix = Unicode('', config=True,
        help="Installation prefix. Overrides --user, --sys-prefix and --system"
    )
    labextensions_dir = Unicode('', config=True,
        help="Full path to labextensions dir (probably use prefix or user)"
    )
    require = Unicode('', config=True, help="require.js module to disable loading")
    system = Bool(False, config=True,
        help="Uninstall specifically from systemwide installation directory"
    )
    
    def _config_file_name_default(self):
        """The default config file name."""
        return 'jupyter_notebook_config'

    def uninstall_labextension(self):
        """Uninstall an labextension from a specific location"""
        kwargs = {
            'user': self.user,
            'sys_prefix': self.sys_prefix,
            'prefix': self.prefix,
            'labextensions_dir': self.labextensions_dir,
            'logger': self.log
        }

        if self.python:
            uninstall_labextension_python(self.extra_args[0], **kwargs)
        else:
            if self.require:
                kwargs['require'] = self.require
            uninstall_labextension(self.extra_args[0], **kwargs)

    def find_uninstall_labextension(self):
        """Uninstall an labextension from an unspecified location"""
        name = self.extra_args[0]
        if self.python:
            _, labexts = _get_labextension_metadata(name)
            changed = False
            for labext in labexts:
                if _find_uninstall_labextension(labext['dest'], logger=self.log):
                    changed = True

                # Also disable it in config.
                for section in NBCONFIG_SECTIONS:
                    _find_disable_labextension(section, labext['require'],
                                              logger=self.log)

        else:
            changed = _find_uninstall_labextension(name, logger=self.log)

        if not changed:
            print("No installed extension %r found." % name)

        if self.require:
            for section in NBCONFIG_SECTIONS:
                _find_disable_labextension(section, self.require,
                                          logger=self.log)

    def start(self):
        if not self.extra_args:
            sys.exit('Please specify an labextension to uninstall')
        elif len(self.extra_args) > 1:
            sys.exit("Only one labextension allowed at a time. "
                     "Call multiple times to uninstall multiple extensions.")
        elif (self.user or self.sys_prefix or self.system or self.prefix
              or self.labextensions_dir):
            # The user has specified a location from which to uninstall.
            try:
                self.uninstall_labextension()
            except ArgumentConflict as e:
                sys.exit(str(e))
        else:
            # Uninstall wherever it is.
            self.find_uninstall_labextension()


class TogglelabextensionApp(BaseExtensionApp):
    """A base class for apps that enable/disable extensions"""
    name = "jupyter labextension enable/disable"
    version = __version__
    description = "Enable/disable an labextension in configuration."

    section = Unicode('notebook', config=True,
          help="""Which config section to add the extension to, 'common' will affect all pages."""
    )
    user = Bool(True, config=True, help="Apply the configuration only for the current user (default)")

    aliases = {'section': 'TogglelabextensionApp.section'}
    
    _toggle_value = None

    def _config_file_name_default(self):
        """The default config file name."""
        return 'jupyter_notebook_config'
    
    def toggle_labextension_python(self, module):
        """Toggle some extensions in an importable Python module.

        Returns a list of booleans indicating whether the state was changed as
        requested.

        Parameters
        ----------
        module : str
            Importable Python module exposing the
            magic-named `_jupyter_labextension_paths` function
        """
        toggle = (enable_labextension_python if self._toggle_value
                  else disable_labextension_python)
        return toggle(module,
                      user=self.user,
                      sys_prefix=self.sys_prefix,
                      logger=self.log)

    def toggle_labextension(self, require):
        """Toggle some a named labextension by require-able AMD module.

        Returns whether the state was changed as requested.

        Parameters
        ----------
        require : str
            require.js path used to load the labextension
        """
        toggle = (enable_labextension if self._toggle_value
                  else disable_labextension)
        return toggle(self.section, require,
                      user=self.user, sys_prefix=self.sys_prefix,
                      logger=self.log)
        
    def start(self):
        if not self.extra_args:
            sys.exit('Please specify an labextension/package to enable or disable')
        elif len(self.extra_args) > 1:
            sys.exit('Please specify one labextension/package at a time')
        if self.python:
            self.toggle_labextension_python(self.extra_args[0])
        else:
            self.toggle_labextension(self.extra_args[0])


class EnablelabextensionApp(TogglelabextensionApp):
    """An App that enables labextensions"""
    name = "jupyter labextension enable"
    description = """
    Enable an labextension in frontend configuration.
    
    Usage
        jupyter labextension enable [--system|--sys-prefix]
    """
    _toggle_value = True


class DisablelabextensionApp(TogglelabextensionApp):
    """An App that disables labextensions"""
    name = "jupyter labextension disable"
    description = """
    Disable an labextension in frontend configuration.
    
    Usage
        jupyter labextension disable [--system|--sys-prefix]
    """
    _toggle_value = None


class ListlabextensionsApp(BaseExtensionApp):
    """An App that lists and validates labextensions"""
    name = "jupyter labextension list"
    version = __version__
    description = "List all labextensions known by the configuration system"
    
    def list_labextensions(self):
        """List all the labextensions"""
        config_dirs = [os.path.join(p, 'nbconfig') for p in jupyter_config_path()]
        
        print("Known labextensions:")
        
        for config_dir in config_dirs:
            head = u'  config dir: {}'.format(config_dir)
            head_shown = False

            cm = BaseJSONConfigManager(parent=self, config_dir=config_dir)
            for section in NBCONFIG_SECTIONS:
                data = cm.get(section)
                if 'load_extensions' in data:
                    if not head_shown:
                        # only show heading if there is an labextension here
                        print(head)
                        head_shown = True
                    print(u'    {} section'.format(section))
                    
                    for require, enabled in data['load_extensions'].items():
                        print(u'      {} {}'.format(
                            require,
                            GREEN_ENABLED if enabled else RED_DISABLED))
                        if enabled:
                            validate_labextension(require, logger=self.log)
    
    def start(self):
        """Perform the App's functions as configured"""
        self.list_labextensions()


_examples = """
jupyter labextension list                          # list all configured labextensions
jupyter labextension install --py <packagename>    # install an labextension from a Python package
jupyter labextension enable --py <packagename>     # enable all labextensions in a Python package
jupyter labextension disable --py <packagename>    # disable all labextensions in a Python package
jupyter labextension uninstall --py <packagename>  # uninstall an labextension in a Python package
"""

class labextensionApp(BaseExtensionApp):
    """Base jupyter labextension command entry point"""
    name = "jupyter labextension"
    version = __version__
    description = "Work with Jupyter notebook extensions"
    examples = _examples

    subcommands = dict(
        install=(InstalllabextensionApp,"Install an labextension"),
        enable=(EnablelabextensionApp, "Enable an labextension"),
        disable=(DisablelabextensionApp, "Disable an labextension"),
        uninstall=(UninstalllabextensionApp, "Uninstall an labextension"),
        list=(ListlabextensionsApp, "List labextensions")
    )

    def start(self):
        """Perform the App's functions as configured"""
        super(labextensionApp, self).start()

        # The above should have called a subcommand and raised NoStart; if we
        # get here, it didn't, so we should self.log.info a message.
        subcmds = ", ".join(sorted(self.subcommands))
        sys.exit("Please supply at least one subcommand: %s" % subcmds)

main = labextensionApp.launch_instance

#------------------------------------------------------------------------------
# Private API
#------------------------------------------------------------------------------


def _should_copy(src, dest, logger=None):
    """Should a file be copied, if it doesn't exist, or is newer?

    Returns whether the file needs to be updated.

    Parameters
    ----------

    src : string
        A path that should exist from which to copy a file
    src : string
        A path that might exist to which to copy a file
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    if not os.path.exists(dest):
        return True
    if os.stat(src).st_mtime - os.stat(dest).st_mtime > 1e-6:
        # we add a fudge factor to work around a bug in python 2.x
        # that was fixed in python 3.x: https://bugs.python.org/issue12904
        if logger:
            logger.warn("Out of date: %s" % dest)
        return True
    if logger:
        logger.info("Up to date: %s" % dest)
    return False


def _maybe_copy(src, dest, logger=None):
    """Copy a file if it needs updating.

    Parameters
    ----------

    src : string
        A path that should exist from which to copy a file
    src : string
        A path that might exist to which to copy a file
    logger : Jupyter logger [optional]
        Logger instance to use
    """
    if _should_copy(src, dest, logger=logger):
        if logger:
            logger.info("Copying: %s -> %s" % (src, dest))
        shutil.copy2(src, dest)


def _safe_is_tarfile(path):
    """Safe version of is_tarfile, return False on IOError.

    Returns whether the file exists and is a tarfile.

    Parameters
    ----------

    path : string
        A path that might not exist and or be a tarfile
    """
    try:
        return tarfile.is_tarfile(path)
    except IOError:
        return False


def _get_labextension_dir(user=False, sys_prefix=False, prefix=None, labextensions_dir=None):
    """Return the labextension directory specified

    Parameters
    ----------

    user : bool [default: False]
        Get the user's .jupyter/labextensions directory
    sys_prefix : bool [default: False]
        Get sys.prefix, i.e. ~/.envs/my-env/share/jupyter/labextensions
    prefix : str [optional]
        Get custom prefix
    labextensions_dir : str [optional]
        Get what you put in
    """
    conflicting = [
        ('user', user),
        ('prefix', prefix),
        ('labextensions_dir', labextensions_dir),
        ('sys_prefix', sys_prefix),
    ]
    conflicting_set = ['{}={!r}'.format(n, v) for n, v in conflicting if v]
    if len(conflicting_set) > 1:
        raise ArgumentConflict(
            "cannot specify more than one of user, sys_prefix, prefix, or labextensions_dir, but got: {}"
            .format(', '.join(conflicting_set)))
    if user:
        labext = pjoin(jupyter_data_dir(), u'labextensions')
    elif sys_prefix:
        labext = pjoin(ENV_JUPYTER_PATH[0], u'labextensions')
    elif prefix:
        labext = pjoin(prefix, 'share', 'jupyter', 'labextensions')
    elif labextensions_dir:
        labext = labextensions_dir
    else:
        labext = pjoin(SYSTEM_JUPYTER_PATH[0], 'labextensions')
    return labext


def _get_labextension_metadata(module):
    """Get the list of labextension paths associated with a Python module.

    Returns a tuple of (the module,             [{
        'section': 'notebook',
        'src': 'mockextension',
        'dest': '_mockdestination',
        'require': '_mockdestination/index'
    }])

    Parameters
    ----------

    module : str
        Importable Python module exposing the
        magic-named `_jupyter_labextension_paths` function
    """
    m = import_item(module)
    if not hasattr(m, '_jupyter_labextension_paths'):
        raise KeyError('The Python module {} is not a valid labextension, '
                       'it is missing the `_jupyter_labextension_paths()` method.'.format(module))
    labexts = m._jupyter_labextension_paths()
    return m, labexts



if __name__ == '__main__':
    main()
