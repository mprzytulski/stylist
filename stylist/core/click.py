from __future__ import absolute_import

import importlib
import os
import pkgutil
import re
from copy import copy
from os.path import dirname, join, abspath

import click
from box import Box
from click import MultiCommand, Group, Context


def list_features():
    """
    Return list of available features supported by stylist
    :return:
    """
    features = {}
    pkgpath = join(dirname(__file__), '..', 'feature')
    for x, _name, y in pkgutil.iter_modules([pkgpath]):
        try:
            cls = _name.title() + 'Feature'
            _module_name = 'stylist.feature.' + _name

            m = importlib.import_module(_module_name)
            features[_name] = getattr(m, cls)
        except ImportError as e:
            print e.message

    return features


class GroupPrototype(object):
    """
    Custom group prototype factory. Custom groups allow to easily pass global parameters to subcommands
    """
    @staticmethod
    def create(help):
        @click.group(cls=CustomGroup)
        @click.option('--working-dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                      help='Changes the folder to operate on.')
        @click.option('--profile', help='Temporary change active profile for given command')
        @click.option('--project-name', help='Overwrite project name')
        def prototype(working_dir=None, profile=None, project_name=None):
            current_ctx = click.get_current_context()
            stylist = current_ctx.obj
            if not isinstance(current_ctx.command, Group):
                stylist.working_dir = working_dir or stylist.working_dir
                stylist.profile = profile or stylist.profile
                stylist.name = project_name or stylist.name

        cli = copy(prototype)
        cli.short_help = help

        return cli


class StylistCli(MultiCommand):
    """
    Custom cli implementation with dynamic command loading and custom context creator.
    """
    def make_context(self, info_name, args, parent=None, **extra):
        """
        Custom context creator - create context and bind active features to it
        """
        for key, value in self.context_settings.items():
            if key not in extra:
                extra[key] = value

        ctx = Context(self, info_name=info_name, parent=parent, **extra)

        for name, cls in list_features().items():
            feature = cls(ctx.obj, **ctx.obj.settings.stylist.features.get(name))
            if feature.installed:
                ctx.obj.features[name] = feature

                if hasattr(feature, 'on_init'):
                    ctx.obj.bind(init=feature.on_init)

                if hasattr(feature, 'on_config'):
                    ctx.obj.bind(config=feature.on_config)

        ctx.obj.emit('init', stylist=ctx.obj)
        ctx.obj.emit('config', stylist=ctx.obj)

        with ctx.scope(cleanup=False):
            self.parse_args(ctx, args)

        return ctx

    def list_commands(self, ctx):
        """
        List available commands
        """
        rv = ctx.obj.features.keys()
        commands_path = abspath(join(dirname(__file__), '..', 'core', 'cmd'))

        for command in [f[:-3] for f in os.listdir(commands_path) if f != '__init__.py' and re.match(r'^\w+\.py$', f)]:
            rv.append(command)

        rv.sort()

        return rv

    def get_command(self, ctx, name):
        """
        Get command using dynamic command loader
        """
        name = name.encode('ascii', 'replace')
        mod = None
        for pattern in ['stylist.core.cmd.{}', 'stylist.feature.{}.cmd']:
            try:
                mod = importlib.import_module(pattern.format(name))
            except ImportError:
                pass

        if not mod or 'stylist.feature.' in mod.__name__ and name not in ctx.obj.features:
            return None

        return mod.cli if hasattr(mod, 'cli') else None


class CustomGroup(Group):
    """ Allow application of options to group with multi command """

    def add_command(self, cmd, name=None):
        """ Hook the added command and put the group options on the command """
        Group.add_command(self, cmd, name=name)

        # add the group parameters to the command
        for param in self.params:
            cmd.params.append(param)

        # hook the command's invoke with our own
        cmd.invoke = self.build_command_invoke(cmd.invoke)

    def build_command_invoke(self, original_invoke):
        def command_invoke(ctx):
            """ insert invocation of group function """

            # separate the group parameters
            params = dict(_params=dict())
            for param in self.params:
                name = param.name
                params[name] = ctx.params[name]
                del ctx.params[name]

            # call the group function with its parameters
            # params = ctx.params
            # ctx.params = ctx.obj['_params']
            # self.invoke(ctx)
            # ctx.params = params

            # now call (invoke) the original command
            original_invoke(ctx)

        return command_invoke
