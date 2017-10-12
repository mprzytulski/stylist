import os
import sys
from copy import copy
from os import listdir
from os.path import isdir, islink, join

import click
import yaml

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.utils import colourize, get_provider
from stylist.wrapper.terraform import Terraform

cli = copy(cli_prototype)
cli.short_help = 'Manage project environments'


@cli.command(help="Show active environment for current working directory")
@stylist_context
def selected(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.secho(
        colourize(ctx.environment)
    )


@cli.command(help="Activate named profile")
@click.argument("name")
@stylist_context
def select(ctx, name, project_name=None, profile=None, working_dir=None):
    """
    @type ctx: stylist.cli.Context
    """
    with open(ctx.environment_file, 'w') as f:
        f.write(name)

    # @todo: check if there is a aws profile matching given env, if not - call create action

    click.secho("Selected profile: {}".format(colourize(name)))


# @cli.command(help="Create deployment profile")
# @click.argument("name")
# @click.option("--provider", default="aws")
# @stylist_context
# def create(ctx, name, provider, project_name=None, profile=None, working_dir=None):
#     """
#     @@ignore_check@@
#     @type ctx: stylist.cli.Context
#     """
#     if not isdir(ctx.config_dir):
#         os.mkdir(ctx.config_dir)
#
#     ctx.environment = name
#
#     if isdir(ctx.profile_dir):
#         logger.error("Profile '{}' already exists".format(name))
#         sys.exit(1)
#
#     provider = get_provider(provider)(ctx)
#
#     values = {}
#     for arg_name, parameter in provider.known_params.items():
#         desc, kwargs = parameter
#         values[arg_name] = str(click.prompt(desc.format(env_name=name), **kwargs))
#
#     provider.dump(values)
#
#     click.get_current_context().invoke(select, name=name)


@cli.command(help="List all available profiles")
@stylist_context
def list(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.echo("All defined environments:")

    for f in ctx.settings.get('stages', []):
        click.secho(
            ("-> " if f == ctx.environment else "   ") + colourize(f)
        )


# @cli.command(name="sync-vars", help="Synchronise configuration variables between profiles")
# @click.argument("source_profile")
# @click.argument("destination_profile")
# @stylist_context
# def sync_vars(ctx, source_profile, destination_profile):
#     try:
#         profiles = _list_profiles(ctx)
#
#         if source_profile not in profiles:
#             raise Exception('Source profile "{}" is missing'.format(source_profile))
#
#         if destination_profile not in profiles:
#             raise Exception('Destination profile "{}" is missing'.format(destination_profile))
#
#         terraform = Terraform(ctx)
#         terraform.sync_vars(source_profile, destination_profile)
#     except Exception as e:
#         logger.error(e.message)
