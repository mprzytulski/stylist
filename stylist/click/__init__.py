from __future__ import absolute_import

import os
import sys
from os.path import dirname, join, abspath, isfile

from click import MultiCommand, Group
from git import Repo, InvalidGitRepositoryError

from stylist import config
from stylist.provider.aws import AWSProvider
from stylist.utils import find_dotenv

CONTEXT_SETTINGS = dict(auto_envvar_prefix='STYLIST')


class Context(object):
    def __init__(self):
        self.working_dir = os.getcwd()
        self.environment = ""
        self.name = None
        self.settings = {}
        self._provider = None
        self.config_filename = 'config.yml'

        path = None
        for p in [".stylist", ".git"]:
            path = find_dotenv(filename=p, path=self.working_dir)
            if path:
                break

        if path:
            self.working_dir = dirname(path)

    @property
    def environment_file(self):
        return join(self.config_dir, 'environment')

    @property
    def config_dir(self):
        return join(self.working_dir, ".stylist")

    @property
    def config_file(self):
        return join(self.config_dir, self.config_filename)

    @property
    def provider(self):
        if not self._provider:
            self._load_provider()

        return self._provider

    def load(self, profile):
        self.environment = profile or self.environment or self._active_environment() or ""

        try:
            self.name = self.name or Repo(self.working_dir) \
                .remote('origin') \
                .url \
                .split('/')[-1] \
                .replace(".git", '') \
                .replace('***REMOVED***', '')
        except InvalidGitRepositoryError:
            from stylist.cli import logger
            self.name = 'unknown'

        self.settings = config.conform(config.get(self.config_filename))

    def _load_provider(self):
        self._provider = AWSProvider(self)
        self._provider.load()
        self._provider.values.update({
            'profile': self.settings.get('provider', {}).get('prefix', '') + self.environment
        })

    def _active_environment(self):
        if not isfile(self.environment_file):
            return 'local'

        with open(self.environment_file) as f:
            return f.readline().strip()


class ComplexCLI(MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(abspath(join(os.path.dirname(__file__), '..', 'commands'))):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                name = filename[4:-3]
                rv.append(name)
        rv.sort()

        return rv

    def get_command(self, ctx, name):
        pass
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('stylist.commands.cmd_' + name, None, None, ['cli'])

            return mod.cli
        except ImportError as e:
            raise e


class GroupWithCommandOptions(Group):
    """ Allow application of options to group with multi command """

    def add_command(self, cmd, name=None):
        """ Hook the added command and put the group options on the command """
        Group.add_command(self, cmd, name=name)

        cmd.require_project = '@@ignore_check@@' not in (cmd.callback.__doc__ or "")

        # add the group parameters to the command
        for param in self.params:
            cmd.params.append(param)

        # hook the command's invoke with our own
        cmd.invoke = self.build_command_invoke(cmd.invoke)
        self.invoke_without_command = True

    def build_command_invoke(self, original_invoke):

        def command_invoke(ctx):
            """ insert invocation of group function """

            # separate the group parameters
            ctx.obj = dict(_params=dict())
            for param in self.params:
                name = param.name
                ctx.obj['_params'][name] = ctx.params[name]
                del ctx.params[name]

            # call the group function with its parameters
            params = ctx.params
            ctx.params = ctx.obj['_params']
            self.invoke(ctx)
            ctx.params = params

            # now call (invoke) the original command
            original_invoke(ctx)

        return command_invoke

    def require_project(self, current_ctx):
        return self.get_command(current_ctx, current_ctx.invoked_subcommand).require_project
