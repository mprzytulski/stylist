from __future__ import absolute_import

import importlib
import os
import pkgutil
import re
import sys
from os.path import dirname, join, abspath

from click import MultiCommand, Group


def list_features(stylist):
    pkgpath = join(dirname(__file__), '..', 'feature')
    features = {}
    for x, _name, y in pkgutil.iter_modules([pkgpath]):
        try:
            cls = _name.title() + 'Feature'
            _module_name = 'stylist.feature.' + _name

            m = importlib.import_module(_module_name)
            features[_name] = getattr(m, cls)(stylist)
        except ImportError:
            pass

    return features


class ComplexCLI(MultiCommand):
    def list_commands(self, ctx):
        rv = []
        commands_path = abspath(join(dirname(__file__), '..', 'commands'))
        features = list_features(ctx.obj)

        for command in [f[4:-3] for f in os.listdir(commands_path) if re.match(r'^cmd_\w+\.py$', f)]:
            if command in features:
                feature = features.get(command)
                if not feature.installed:
                    continue

                ctx.object.features[command] = feature

            rv.append(command)

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


class GroupWithCommandOptions(Group):
    """ Allow application of options to group with multi command """

    # def add_command(self, cmd, name=None):
    #     """ Hook the added command and put the group options on the command """
    #     Group.add_command(self, cmd, name=name)
    #
    #     # cmd.require_project = '@@ignore_check@@' not in (cmd.callback.__doc__ or "")
    #
    #     # add the group parameters to the command
    #     for param in self.params:
    #         cmd.params.append(param)
    #
    #     # hook the command's invoke with our own
    #     cmd.invoke = self.build_command_invoke(cmd.invoke)
    #     self.invoke_without_command = True

    # def build_command_invoke(self, original_invoke):
    #
    #     def command_invoke(ctx):
    #         """ insert invocation of group function """
    #
    #         # separate the group parameters
    #         ctx.obj = dict(_params=dict())
    #         for param in self.params:
    #             name = param.name
    #             ctx.obj['_params'][name] = ctx.params[name]
    #             del ctx.params[name]
    #
    #         # call the group function with its parameters
    #         params = ctx.params
    #         ctx.params = ctx.obj['_params']
    #         self.invoke(ctx)
    #         ctx.params = params
    #
    #         # now call (invoke) the original command
    #         original_invoke(ctx)
    #
    #     return command_invoke
    #
    # def require_project(self, current_ctx):
    #     return self.get_command(current_ctx, current_ctx.invoked_subcommand).require_project
