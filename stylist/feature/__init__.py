import importlib
import os
import pkgutil
import tempfile
from os import mkdir
from os.path import exists, join

import click
from click import style
from git import Git, Repo
from jinja2 import Environment, FileSystemLoader

from stylist.wrapper.terraform import Terraform


class Templates(object):
    REPOSITORY = 'git@github.com:ThreadsStylingLtd/templates.git'

    def __init__(self, version='master'):
        self.version = version

        # self.destination = '/Users/me/projects/threads/templates'
        self.destination = join(tempfile.gettempdir(), "stylist-templates")

        self.env = Environment(loader=FileSystemLoader(self.destination))
        self._init_repository()

    def _init_repository(self):
        if not exists(self.destination):
            mkdir(self.destination)
            Git().clone(Templates.REPOSITORY, self.destination)

        repo = Repo(self.destination)
        repo.git.checkout(self.version)
        repo.remote("origin").pull()

    def get_template(self, name):
        return self.env.get_template(name)

    def get_module_source(self, module_name):
        return Templates.REPOSITORY + "//terraform_modules/" + module_name


class Feature(object):
    def __init__(self, version):
        self.templates = Templates(version)

    def enable_terraform(self, ctx, module_name, module_alias):
        terraform = Terraform(ctx, self.templates)
        terraform.setup()

        module_alias = click.prompt(style('Terraform', fg='blue') + " | ECS Service name", default=module_alias)

        terraform.configure_module(module_name, module_alias)


FEATURES = {}


def get_feature(name, version):
    return FEATURES.get(name)(version)


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
