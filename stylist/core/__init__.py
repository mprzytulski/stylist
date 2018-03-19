from __future__ import absolute_import

import os
import sys
from genericpath import isfile
from os.path import join, realpath

import click
from box import Box
from git import Repo, InvalidGitRepositoryError
from pydispatch import Dispatcher

from stylist import config
from stylist.config import schema
from stylist.core.containers import GlobalContainer, ConfigStorageContainer
from stylist.core.providers import ConfigStorage, DockerRepositoryProvider
from stylist.feature.config.lib import parametrise_name
from stylist.utils import find_dotenv


class Stylist(Dispatcher):
    _events_ = ['init', 'config']

    def __init__(self):
        self.cwd = os.getcwd()
        # @todo: that should be simplified
        self.working_dir = realpath(join(find_dotenv(filename='.git', path=self.cwd, limit=self.cwd), '..')) or self.cwd
        self.config_filename = 'config.yml'
        self.settings = self._get_settings()
        self.name = self._get_name()
        self.features = Box({})
        self.profile = self._get_active_profile()
        self.containers = Box({
            'main': GlobalContainer(),
            'config': ConfigStorageContainer(),
            # 'docker_repository': ConfigStorageContainer(),
        })

    def __getattr__(self, item):
        return self.containers.get(item)

    @property
    def environment_file(self):
        return join(self.local_config_dir, 'environment')

    @property
    def local_config_dir(self):
        return join(self.working_dir, ".stylist")

    @property
    def config_file(self):
        return join(self.local_config_dir, self.config_filename)

    def config_provider(self):
        return getattr(self.containers.get('config'), self.settings.providers.config or 'ssm')()

    @property
    def service_name(self):
        return 'service:{}'.format(parametrise_name(self.name))

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
            return Box(config.conform(config.get(self.config_file, self.config_filename)), default_box=True)
        except schema.SchemaError as e:
            click.secho(e.message, fg='yellow')
            sys.exit(1)
