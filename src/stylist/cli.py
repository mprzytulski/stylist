import logging
import os
import sys
from glob import glob
from os import readlink
from os.path import join, basename

import click
import click_log

from stylist.lib.utils import get_provider

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(auto_envvar_prefix='STYLIST')


class Context(object):
    def __init__(self):
        self.working_dir = os.getcwd()
        self.environment = None
        self.config_dir = ""
        self.profile_dir = ""
        self.loaded = False

    def load(self, profile):
        if self.loaded:
            return

        self.config_dir = join(self.working_dir, ".stylist")
        self.environment = profile or self._active_environment()
        self.profile_dir = join(self.config_dir, self.environment)
        self._load_provider()
        self.loaded = True

    def _load_provider(self):
        configs = glob(join(self.profile_dir, "config.*"))
        if not configs:
            return

        config_path = configs[0]
        provider_type = basename(config_path).split(".")[1]
        self.provider = get_provider(provider_type)(self)
        self.provider.load(config_path)

    def _active_environment(self):
        try:
            return readlink(join(self.config_dir, "selected"))
        except OSError:
            return None


stylist_context = click.make_pass_decorator(Context, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'commands'))


class ComplexCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                rv.append(filename[4:-3])
        rv.sort()

        return rv

    def get_command(self, ctx, name):
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('stylist.commands.cmd_' + name, None, None, ['cli'])
            return mod.cli
        except ImportError as e:
            raise e


class GroupWithCommandOptions(click.Group):
    """ Allow application of options to group with multi command """

    def add_command(self, cmd, name=None):
        """ Hook the added command and put the group options on the command """
        click.Group.add_command(self, cmd, name=name)

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


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click_log.init(__name__)
def cli():
    pass
