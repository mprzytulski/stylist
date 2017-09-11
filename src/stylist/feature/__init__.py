import importlib
import os
import pkgutil
import shutil
from os import mkdir
from os.path import join, exists

from git import Git, Repo


class Templates(object):
    REPOSITORY = 'git@github.com:ThreadsStylingLtd/templates.git'

    def __init__(self, version):
        self.version = version
        self.destination = '/Users/me/projects/threads/templates'
        # self.destination = join(tempfile.gettempdir(), "stylist-templates")
        # self._init_repository()

    def _init_repository(self):
        if not exists(self.destination):
            mkdir(self.destination)
            Git().clone(Templates.REPOSITORY, self.destination)

        repo = Repo(self.destination)
        repo.git.checkout(self.version)
        repo.remote("origin").pull()


class Feature(object):
    def __init__(self):
        self.templates = None

    def enable_terraform(self, ctx):
        shutil.copytree(join(self.templates.destination, 'terraform'), join(ctx.working_dir, 'terraform'))

    def terraform_install_module(self, ctx, module_name, required=None):
        pass


FEATURES = {}


def get_feature(name):
    return FEATURES.get(name)


pkgpath = os.path.dirname(__file__)
for x, _name, y in pkgutil.iter_modules([pkgpath]):
    try:
        cls = _name.title() + 'Feature'
        _module_name = __name__ + '.' + _name
        m = importlib.import_module(_module_name)
        FEATURES[_name] = getattr(m, cls)()
    except ImportError as e:
        raise e
        pass
