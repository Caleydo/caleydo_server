###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from builtins import map
from past.builtins import basestring
from builtins import object
from ._utils import replace_variables
from .config import view

cc = view('phovea_server')


def is_disabled_plugin(p):
  import re

  def check(disable):
    return isinstance(disable, basestring) and re.match(disable, p.id)

  return any(map(check, cc.disable['plugins']))


def is_disabled_extension(extension, extension_type, p):
  import re

  if is_disabled_plugin(p):
    return True

  def check_elem(k, v):
    vk = extension_type if k == 'type' else extension[k]
    return re.match(v, vk)

  def check(disable):
    if isinstance(disable, basestring):
      return re.match(disable, extension['id'])
    return all(check_elem(k, v) for k, v in list(disable.items()))

  return any(map(check, cc.disable['extensions']))


def _resolve_server_config(d, vars={}):
  import six
  if isinstance(d, six.string_types):  # not a string
    return replace_variables(d, vars)
  elif isinstance(d, list):
    return [_resolve_server_config(i) for i in d]
  elif isinstance(d, dict):
    for k, v in list(d.items()):
      d[k] = _resolve_server_config(v)
    return d
  return d


# extend a dictionary recursivly
def _extend(target, w):
  for k, v in list(w.items()):
    if isinstance(v, dict):
      if k not in target:
        target[k] = _extend({}, v)
      else:
        target[k] = _extend(target[k], v)
    else:
      target[k] = v
  return target


class DirectoryPlugin(object):
  def __init__(self, package_file):
    import json
    import os.path as p
    folder = p.dirname(package_file)
    with open(package_file) as f:
      pkg = json.load(f)
    self.id = pkg['name']
    self.pkg = pkg
    self.name = self.id
    desc = pkg.get('description', '').split('\n')
    self.title = desc.pop(0) if len(desc) > 1 else self.name
    self.description = '\n'.join(desc)
    self.homepage = pkg.get('homepage')
    self.version = pkg['version']
    self.extensions = []
    self.repository = pkg.get('repository', {}).get('url')
    self.folder = folder

  def is_app(self):
    import os.path as p
    f = p.join(self.folder, 'build', 'index.html')
    return p.exists(f)

  def config_file(self):
    import os.path as p
    f = p.join(self.folder, 'config.json')
    if p.exists(f):
      return f
    f = p.join(self.folder, self.id, 'config.json')
    return f if p.exists(f) else None

  def register(self, reg):
    import os.path as p
    import sys

    def regfile(f):
      if not p.exists(f):
        return
      # append path ../__init__.py
      sys.path.append(p.abspath(p.dirname(p.dirname(f))))
      import importlib
      m = importlib.import_module(self.id)
      if hasattr(m, 'phovea'):
        m.phovea(reg)

    regfile(p.join(self.folder, '__init__.py'))
    regfile(p.join(self.folder, self.id, '__init__.py'))


class EntryPointPlugin(object):
  def __init__(self, entry_point, config_entry_point):
    self.id = entry_point.name
    self.name = self.id
    self.title = self.name
    self.description = ''
    self.version = ''
    self.extensions = []
    self.repository = None
    self._loader = entry_point.load
    self._config = config_entry_point.load

    # guess folder
    f = self.config_file()
    import os.path
    self.folder = os.path.dirname(f) if f else '.'

  def is_app(self):
    return False

  def config_file(self):
    if self._config is not None:
      return self._config()()
    return None

  def register(self, reg):
    self._loader(reg)


class RegHelper(object):
  def __init__(self, plugin):
    self._items = []
    self._plugin = plugin

  def __iter__(self):
    return iter(self._items)

  def append(self, type_, id_, module_, desc=None):
    desc = {} if desc is None else desc
    desc['type'] = type_
    desc['id'] = id_
    desc['module'] = module_
    desc['plugin'] = self._plugin
    self._items.append(desc)


class PluginMetaData(object):
  def __init__(self):
    self.plugins = []

    entrypoints = self.find_entry_point_plugins()
    self.plugins.extend(p for p in entrypoints if not is_disabled_plugin(p))

    neigbhors = self.find_neighbor_plugins()
    self.plugins.extend(p for p in neigbhors if not is_disabled_plugin(p))

    self.plugins.sort(key=lambda p: p.id)

    self.server_extensions = []
    for p in self.plugins:
      reg = RegHelper(p)
      p.register(reg)
      ext = [r for r in reg if not is_disabled_extension(r, 'python', p)]
      p.extensions = ext
      self.server_extensions.extend(ext)

  def find_entry_point_plugins(self):
    import pkg_resources as p
    configs = {ep.name: ep for ep in p.iter_entry_points(group='phovea.config')}
    return [EntryPointPlugin(ep, configs.get(ep.name)) for ep in p.iter_entry_points(group='phovea.registry')]

  def find_neighbor_plugins(self):
    import os.path as p
    import glob
    import itertools
    prefix = ['./', '../', '../../']
    suffix = ['', 'p/', 'public/']
    files = []
    for pre, s in itertools.product(prefix, suffix):
      files.extend((p.abspath(pi) for pi in glob.glob(pre + s + '*/package.json')))
    # files contains all plugins
    return [DirectoryPlugin(pi) for pi in files]


def parse():
  p = PluginMetaData()
  return p
