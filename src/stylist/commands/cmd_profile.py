import os
import sys
from os import listdir, readlink
from os.path import isdir, islink, join

import click
import yaml

from stylist.cli import pass_context, logger, GroupWithCommandOptions
from stylist.commands import ensure_project_directory, NotProjectDirectoryException, global_options
from stylist.lib.utils import colourize
from stylist.provider import get


@click.group(cls=GroupWithCommandOptions, short_help='Manage project environments')
@global_options
@pass_context
def cli(ctx, working_dir):
    if working_dir is not None:
        try:
            if click.get_current_context().invoked_subcommand != 'create':
                ensure_project_directory(working_dir)
            ctx.working_dir = working_dir
        except NotProjectDirectoryException as e:
            logger.error(e.message)
            sys.exit(1)


@cli.command(help="Show active environment for current working directory")
@pass_context
def selected(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.secho(
        colourize(ctx.environment)
    )


@cli.command(help="Activate named profile")
@click.argument("name")
@pass_context
def select(ctx, name, working_dir=None):
    """
    @type ctx: stylist.cli.Context
    """
    profile_path = join(ctx.config_dir, name)
    if not isdir(profile_path):
        logger.error("Unable to locate '{}' environment".format(name))
        sys.exit(1)

    selected_path = join(ctx.config_dir, "selected")
    if islink(selected_path):
        os.remove(selected_path)

    os.symlink(name, selected_path)
    click.secho(click.style("All done.", fg="green"))


@cli.command(help="Create deployment profile")
@click.argument("name")
@click.option("--provider", default="aws")
@pass_context
def create(ctx, name, provider):
    """
    @type ctx: stylist.cli.Context
    """
    if not isdir(ctx.config_dir):
        os.mkdir(ctx.config_dir)

    profile_path = join(ctx.config_dir, name)
    if isdir(profile_path):
        logger.error("Profile '{}' already exists".format(name))
        sys.exit(1)

    provider = get(provider)

    values = {}
    for arg_name, parameter in provider.get_params().iteritems():
        desc, kwargs = parameter
        values[arg_name] = click.prompt(desc, **kwargs)

    os.mkdir(profile_path)

    with open(join(profile_path, "config"), "w+") as f:
        yaml.dump({
            "provider": values
        }, f)

    selected_name = ctx.environment

    if not selected_name:
        click.get_current_context().invoke(select, name=name)


@cli.command(help="List all available profiles")
@pass_context
def list(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.echo("All defined environments:")

    selected_env = selected_env_name(ctx)

    for f in filter(lambda x: not islink(join(ctx.config_dir, x)), listdir(ctx.config_dir)):
        click.secho(
            ("-> " if f == selected_env else "   ") + colourize(f)
        )


@cli.command()
@pass_context
def prompt(ctx):
    pass
