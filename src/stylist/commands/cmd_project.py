import os

import click
from os.path import join

import git
import sys

from click import Path

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.lib.click.types import Boolean
from stylist.lib.project import Templates
from stylist.lib.project.feature import get_feature

cli = cli_prototype
cli.short_help = "Stylist project helper"

TEMPLATES_REPO = 'git@github.com:ThreadsStylingLtd/stylist.git'


@cli.command(help="Initialise new project")
@click.argument("git_repo"
                "sitory")
@click.option("--path", type=Path(), help="Destination directory in which project should be initialised")
@click.option("--templates-version", default="master",
              help="Git branch / tag of templates repository which should be used for init")
@stylist_context
def init(ctx, git_repository, path, templates_version='master'):
    """
    @@ignore_check@@
    """
    try:
        path = path or join(os.getcwd(), git_repository.split('/')[-1].replace('.git', ''))

        ctx.working_dir = path

        if os.path.exists(path):
            logger.error('Destination "{}" exists, use update instead'.format(path))
            # sys.exit(1)

        # git.Git().clone(git_repository, path)

        # click.secho('Git repository cloned to: "{}"'.format(path), fg="green")
        #
        features = {}
        for feature in ('terraform', 'serverless', 'docker'):
            # features[feature] = click.prompt("Enable {} support".format(feature), type=Boolean())
            features[feature] = True

        settings = {
            "features": {k: {} for k, v in features.items() if v},
            "templates": {
                "version": templates_version,
                "files": {}
            }
        }

        # print get_feature('terraform')

        templates = Templates(templates_version)

        for name, feature in settings.get('features').items():
            get_feature(name).setup(ctx, templates)
    except Exception as e:
        logger.error("Failed to create project - you may need clean it up manually. \n{}".format(e))
        sys.exit(1)


@cli.command(name="update", help="Update project")
@stylist_context
def update(ctx):
    pass
