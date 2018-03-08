import os
import sys
from subprocess import call

import click
import git
import yaml
from click import Path

# import stylist.provider.sentry as sentry
# from stylist.cli import logger
# from stylist.commands import GroupPrototype
from stylist.core.click import GroupPrototype

cli = GroupPrototype.create('Stylist project helper')

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
@click.pass_obj
def init(ctx, git_repository, path):
    """
    @@ignore_check@@
    """

    return

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

#
# @cli.command('add-feature', help="Add new feature to current project")
# @click.argument('feature')
# @click.argument('init_args', nargs=-1, type=click.UNPROCESSED)
# @click.pass_obj
# def add_feature(ctx, feature, init_args):
#     try:
#         f = get_feature(feature, ctx)
#         f.setup(init_args)
#
#         click.secho('Feature "{}" has been added to your project'.format(feature), fg='green')
#     except FeatureException as e:
#         click.secho(e.message, fg='red')
#         sys.exit(1)
#
#
# @cli.command('list-features', help="List all available features")
# @click.pass_obj
# def list_features(stylist):
#     features = []
#     for feature, inst in list_features().items():
#         features.append([
#             feature,
#             str(inst.__doc__ or '').strip(),
#             click.style('true', fg='green') if feature in stylist.features else 'false'
#         ])
#
#     click.secho(
#         table("STYLIST FEATURES", features, ["FEATURE", "DESCRIPTION", "INSTALLED"]).table
#     )
