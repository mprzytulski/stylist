import click
import os

_global_options = [
    click.option('--working-dir', type=click.Path(exists=True, file_okay=False, resolve_path=True),
                 help='Changes the folder to operate on.')
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
