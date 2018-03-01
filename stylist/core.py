from __future__ import absolute_import

import os
import sys
from genericpath import isfile
from os.path import join

import click
from git import Repo, InvalidGitRepositoryError

from stylist import config
from stylist.config import schema
from stylist.utils import find_dotenv


class Stylist(object):
    def __init__(self):
        self.cwd = os.getcwd()
        # @todo: that should be simplified
        self.working_dir = find_dotenv(filename='.git', path=self.cwd, limit=self.cwd) or self.cwd
        self.config_filename = 'config.yml'
        self.settings = self._get_settings()
        self.name = self._get_name()
        self.features = {}

    @property
    def environment_file(self):
        return join(self.local_config_dir, 'environment')

    @property
    def local_config_dir(self):
        return join(self.working_dir, ".stylist")

    @property
    def config_file(self):
        return join(self.local_config_dir, self.config_filename)

    #     @property
    #     def provider(self):
    #         if not self._provider:
    #             self.set_provider(self.environment)
    #
    #         return self._provider
    #
    #     def set_provider(self, profile):
    #         self._provider = AWSProvider(self)
    #         self._provider.load()
    #         self._provider.values.update({
    #             'profile': self.settings.get('stylist', {}).get('provider', {}).get('prefix', '') + profile
    #         })

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

    def _active_environment(self):
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
