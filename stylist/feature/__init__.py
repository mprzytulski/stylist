import importlib
import os
import pkgutil
import re
import tempfile
from os import mkdir
from os.path import exists, join, dirname, abspath

from git import Git, Repo
from jinja2 import Environment, FileSystemLoader

from stylist.wrapper.terraform import Terraform


class Templates(object):
    def __init__(self, ctx):
        self.ctx = ctx

        self.terraform_modules_source = abspath(ctx.settings.get('terraform', {}).get(
            'templates',
            join(dirname(__file__), '..', '..', 'templates', 'terraform_modules')
        ))

        self.terraform_user_remote_source = \
            re.match('^https?://', self.terraform_modules_source) or self.terraform_modules_source.endswith('.git')

        if self.terraform_user_remote_source:
            self.terraform_local_modules_source = join(tempfile.gettempdir(), "stylist-templates")
            self._init_repository(self.terraform_modules_source, self.terraform_local_modules_source)
        else:
            self.terraform_local_modules_source = self.terraform_modules_source

        self.env = Environment(loader=FileSystemLoader([
            join(dirname(__file__), '..', '..', 'templates', 'internal'),
            # self.local_templates_source
        ]))

    def _init_repository(self, source, destination):
        if not exists(destination):
            mkdir(destination)
            Git().clone(source, destination)

        repo = Repo(destination)
        repo.remote("origin").pull()

    def get_template(self, name):
        return self.env.get_template(name)

    def get_module_source(self, module_name):
        return self.terraform_modules_source + ("//" if self.terraform_user_remote_source else "/") + module_name


class Feature(object):
    def __init__(self, ctx):
        self.templates = Templates(ctx)
        self.terraform = Terraform(ctx, self.templates)

    def enable_terraform(self, ctx, module_name=None, module_alias=None):
        self.terraform.configure_module(module_name, module_alias)


FEATURES = {}


def get_feature(name, ctx):
    return FEATURES.get(name)(ctx)


pkgpath = os.path.dirname(__file__)
for x, _name, y in pkgutil.iter_modules([pkgpath]):
    try:
        cls = _name.title() + 'Feature'
        _module_name = __name__ + '.' + _name
        m = importlib.import_module(_module_name)
        FEATURES[_name] = getattr(m, cls)
    except ImportError as e:
        raise e
        pass
