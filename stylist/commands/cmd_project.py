import os
import sys
from copy import copy
from subprocess import call

import click
import git
import yaml
from click import Path

import stylist.provider.sentry as sentry
from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.feature import get_feature, FEATURES, FeatureException
from stylist.utils import table

cli = copy(cli_prototype)
cli.short_help = 'Stylist project helper'

TEMPLATES_REPO = 'git@github.com:ThreadsStylingLtd/stylist.git'

GIT_IGNORE = """
.stylist/environment
terraform/.tfupdate
terraform/.terraform/environment
terraform/.terraform/modules
terraform/.terraform/plugins/*
!terraform/.terraform/plugins/*/lock.json
"""


@cli.command(help='Initialise new project')
@click.argument('git_repository', default='.')
@click.option('--path', type=Path(), help='Destination directory in which project should be initialised')
@stylist_context
def init(ctx, git_repository, path):
    """
    @@ignore_check@@
    """

    try:
        if git_repository == '.':
            path = os.getcwd()
        elif not path:
            path = os.path.join(os.getcwd(), git_repository.split('/')[-1].replace('.git', ''))

        ctx.working_dir = path

        if git_repository != '.':
            git.Git().clone(git_repository, path)

            click.secho('Git repository cloned to: "{}"'.format(path), fg='green')

        if not os.path.exists(os.path.join(ctx.working_dir, '.stylist')):
            prefix = click.prompt(click.style('Prefix name for environments', fg='blue'), default='')

            try:
                os.makedirs(ctx.config_dir)
            except:
                pass

            stylist_settings = {'provider': {'type': 'aws', 'prefix': str(prefix)},
                                'stages': ['prod', 'uat', 'staging']}

            ctx.settings.update({'stylist': stylist_settings})

            with open(ctx.config_file, 'w+') as f:
                yaml.dump({'stylist': stylist_settings}, f)

            def deal_with_gitignore():
                gitignore_path = os.path.join(path, '.gitignore')
                mode = 'a' if os.path.isfile(gitignore_path) else 'w'

                with open(gitignore_path, mode) as f:
                    f.write(GIT_IGNORE)

                for to_add in ('.gitignore', '.stylist'):
                    call(['git', 'add', to_add])

            deal_with_gitignore()

            from stylist.commands.cmd_profile import select
            click.get_current_context().invoke(select, name='local')

            if ctx.settings.get('sentry'):
                sentry.proj_init_integration(ctx)
    except Exception as e:
        logger.error('Failed to create project - you may need clean it up manually. \n{}'.format(e))
        sys.exit(1)


@cli.command('add-feature', help="Add new feature to current project")
@click.argument('feature', type=click.Choice(FEATURES.keys()))
@stylist_context
def add_feature(ctx, feature):
    try:
        f = get_feature(feature, ctx)
        f.setup()

        click.secho('Feature "{}" has been added to your project'.format(feature), fg='green')
    except FeatureException as e:
        click.secho(e.message, fg='red')
        sys.exit(1)


@cli.command('list-features', help="List all available features")
@stylist_context
def list_features(ctx):
    features = []
    for feature, inst in FEATURES.items():
        features.append([
            feature,
            str(inst.__doc__ or '').strip(),
            click.style('true', fg='green') if get_feature(feature, ctx).installed else 'false'
        ])

    click.secho(
        table("STYLIST FEATURES", features, ["FEATURE", "DESCRIPTION", "INSTALLED"]).table
    )
