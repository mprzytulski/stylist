import os
from os.path import join, isdir

import click
import git
import yaml
from click import Path

from stylist.helper.git import resolve_repository_name, add_to_gitignore

IGNORE_FILES = [
    '.stylist/environment'
]


@click.command(help='Initialise new project')
@click.argument('git_repository', default='.')
@click.option('--path', type=Path(), help='Destination directory in which project should be initialised')
@click.pass_obj
def cli(stylist, git_repository, path):
    if git_repository != '.':
        stylist.name = resolve_repository_name(git_repository)
        stylist.working_dir = join(os.getcwd(), stylist.name)

    if isdir(join(stylist.working_dir, '.stylist')):
        click.secho('Directory is already under stylist control', fg='yellow')
        return 1

    click.secho('Initialising new stylist project under {}'.format(stylist.working_dir), fg='green')

    if not isdir(join(stylist.working_dir, '.git')):
        click.secho("Cloning git repository: {} to {}", format(git_repository, path or stylist.working_dir), fg='blue')
        git.Git().clone(git_repository, stylist.working_dir)

    repo = git.Git(stylist.working_dir)

    if not isdir(stylist.local_config_dir):
        os.makedirs(stylist.local_config_dir)

        stylist_settings = {'stages': ['prod', 'uat', 'staging']}

        with open(stylist.config_file, 'w+') as f:
            yaml.dump({'stylist': stylist_settings}, f)

        add_to_gitignore(join(stylist.working_dir, '.gitignore'), IGNORE_FILES)
        repo.add('.gitignore')
        repo.add('.stylist')

    click.secho("Done", fg='green')
