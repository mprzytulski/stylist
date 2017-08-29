import os
import sys
from os import listdir
from os.path import isdir, islink, join

import click

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.lib.utils import colourize, get_provider

cli = cli_prototype
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
def select(ctx, name):
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
@stylist_context
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

    provider = get_provider(provider)()

    values = {}
    for arg_name, parameter in provider.known_params.items():
        desc, kwargs = parameter
        values[arg_name] = click.prompt(desc, **kwargs)

    provider.dump(values)

    if not ctx.environment:
        click.get_current_context().invoke(select, name=name)


@cli.command(help="List all available profiles")
@stylist_context
def list(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.echo("All defined environments:")

    for f in filter(lambda x: not islink(join(ctx.config_dir, x)), listdir(ctx.config_dir)):
        click.secho(
            ("-> " if f == ctx.environment else "   ") + colourize(f)
        )


@cli.command()
@stylist_context
def prompt(ctx):
    pass
