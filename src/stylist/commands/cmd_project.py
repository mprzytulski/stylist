import os

import click
from os.path import join

import git
import sys

from click import Path

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.commands.cmd_profile import create
from stylist.lib.click.types import Boolean
from stylist.lib.project import Templates
from stylist.lib.project.feature import get_feature, FEATURES

cli = cli_prototype
cli.short_help = "Stylist project helper"

TEMPLATES_REPO = 'git@github.com:ThreadsStylingLtd/stylist.git'


@cli.command(help="Initialise new project")
@click.argument("git_repository")
@click.option("--path", type=Path(), help="Destination directory in which project should be initialised")
@click.option("--templates-version", default="master",
              help="Git branch / tag of templates repository which should be used for init")
@stylist_context
def init(ctx, git_repository, path, templates_version='master'):
    """
    @@ignore_check@@
    """
    try:
        if git_repository == ".":
            path = os.getcwd()
        elif path:
            pass
        else:
            path = join(os.getcwd(), git_repository.split('/')[-1].replace('.git', ''))

        ctx.working_dir = path

        if git_repository != ".":
            git.Git().clone(git_repository, path)

            click.secho('Git repository cloned to: "{}"'.format(path), fg="green")

        if not os.path.exists(join(ctx.working_dir, ".stylist")):
            click.get_current_context().invoke(create, name="local")
    except Exception as e:
        logger.error("Failed to create project - you may need clean it up manually. \n{}".format(e))
        sys.exit(1)


@cli.command("add-feature")
@click.argument("feature", type=click.Choice(FEATURES.keys()))
@click.option("--templates-version", default="master",
              help="Git branch / tag of templates repository which should be used for init")
@stylist_context
def add_feature(ctx, feature, templates_version):
    templates = Templates(templates_version)

    f = get_feature(feature)
    f.setup(ctx, templates)
