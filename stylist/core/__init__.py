from __future__ import absolute_import

import os
import sys
import dependency_injector.containers as containers
from genericpath import isfile
from os.path import join, realpath

import click
from git import Repo, InvalidGitRepositoryError
from pydispatch import Dispatcher

from stylist import config
from stylist.config import schema
from stylist.core.providers import ConfigStorage, DockerRepositoryProvider
from stylist.utils import find_dotenv


class TaggedDynamicContainer(containers.DynamicContainer):
    def add(self, service, tags):
        setattr(self, *service)


class Stylist(Dispatcher):
    _events_ = ['configure', 'load']

    def __init__(self):
        self.cwd = os.getcwd()
        # @todo: that should be simplified
        self.working_dir = realpath(join(find_dotenv(filename='.git', path=self.cwd, limit=self.cwd), '..')) or self.cwd
        self.config_filename = 'config.yml'
        self.settings = self._get_settings()
        self.name = self._get_name()
        self.features = {}
        self.profile = self._get_active_profile()
        self.container = containers.DynamicContainer()

    @property
    def environment_file(self):
        return join(self.local_config_dir, 'environment')

    @property
    def local_config_dir(self):
        return join(self.working_dir, ".stylist")

    @property
    def config_file(self):
        return join(self.local_config_dir, self.config_filename)

    def _get_name(self):
        try:
            name = Repo(self.working_dir) \
                .remote('origin') \
                .url \
                .split('/')[-1] \
                .replace(".git", '')

            for _rep in self.settings.get('stylist', {}).get('name_exclusion', []):
                name = name.replace(_rep, '')

        except InvalidGitRepositoryError:
            name = 'unknown'

        return name

    def _get_active_profile(self):
        if not isfile(self.environment_file):
            return 'local'

        with open(self.environment_file) as f:
            return f.readline().strip()

    def _get_settings(self):
        try:
            return config.conform(config.get(self.config_file, self.config_filename))
        except schema.SchemaError as e:
            click.secho(e.message, fg='yellow')
            sys.exit(1)
