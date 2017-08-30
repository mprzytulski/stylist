import os

import click
from os.path import join

import git
import sys

from click import Path

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype

cli = cli_prototype
cli.short_help = "Stylist project helper"

TEMPLATES_REPO = 'git@github.com:ThreadsStylingLtd/stylist.git'


@cli.command(help="Initialise new project")
@click.argument("git_repo"
                "sitory")
@click.option("--path", type=Path(), help="Destination directory in which project should be initialised")
@stylist_context
def init(ctx, git_repository, path):
    """
    @@ignore_check@@
    """
    path = path or join(os.getcwd(), git_repository.split('/')[-1].replace('.git', ''))

    if os.path.exists(path):
        logger.error('Destination "{}" exists, use update instead'.format(path))
        sys.exit(1)

    git.Git().clone(git_repository, path)

    click.secho('Git repository cloned to: "{}"'.format(path), fg="green")
    # str(click.prompt(""))
    # 1. ask for repo name
    # 2. clone repo to given location
    # 3. ask for features


@cli.command(name="update", help="Update project templates")
@stylist_context
def update(ctx):
    pass
