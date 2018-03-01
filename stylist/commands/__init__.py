import os
import sys

import click

# from stylist.cli import logger
from stylist.click import GroupWithCommandOptions

_global_options = [
    click.option('--working-dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                 help='Changes the folder to operate on.'),
    click.option('--profile', help='Temporary change active profile for given command'),
    click.option('--project-name', help='Overwrite project name')
]


def global_options(func):
    for option in reversed(_global_options):
        func = option(func)
    return func


class NotProjectDirectoryException(Exception):
    pass


def ensure_project_directory(dir):
    if not os.path.isdir(os.path.join(dir, '.stylist')):
        raise NotProjectDirectoryException("Given directory is not under a stylist control")


@click.group(cls=GroupWithCommandOptions)
@global_options
@click.pass_obj
def cli_prototype(ctx, working_dir, profile, project_name):
    working_dir = working_dir or ctx.working_dir
    try:
        current_ctx = click.get_current_context()

        if isinstance(current_ctx.command, GroupWithCommandOptions) and current_ctx.command.require_project(
                current_ctx):
            ensure_project_directory(working_dir)
        ctx.working_dir = working_dir
        ctx.name = project_name
    except NotProjectDirectoryException as e:
        logger.error(e.message)
        sys.exit(1)

    ctx.load(profile)
