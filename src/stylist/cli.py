import os
import sys
import click
import click_log
import logging

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(auto_envvar_prefix='STYLIST')


class Context(object):
    def __init__(self):
        self.working_dir = os.getcwd()

    @property
    def config_dir(self):
        return os.path.join(self.working_dir, '.stylist')


pass_context = click.make_pass_decorator(Context, ensure=True)
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
        except ImportError:
            return
        return mod.cli


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
