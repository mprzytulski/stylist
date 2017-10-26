import sys
import glob
from copy import copy
from datetime import datetime
from os.path import join

import click
from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.wrapper.docker import Docker, NotADockerProjectException, DockerException

cli = copy(cli_prototype)
cli.short_help = 'Docker image helper'


@cli.command(help='Build docker image using Dockerfile')
@click.option('--tag', default=datetime.now().strftime('%Y%m%d_%H%M'))
@click.option('--ask', is_flag=True, help='Ask which repository to build')
@click.option('--force-stage', is_flag=True, default=False,
              help='Add stage to repository name even if --subproject has been specified')
@click.option('--subproject', default=None, help='Build docker image located in named subdirectory / project')
@stylist_context
def build(ctx, tag, ask, subproject, force_stage):
    """
    @type ctx: stylist.cli.Context
    @type tag: string
    @type ask: string

    @@ignore_check@@
    """
    click.secho('Building docker container', fg='blue')

    docker_files = _get_docker_files(ctx, ask, subproject)
    try:
        docker = Docker(ctx, subproject, force_stage)
        for docker_file in docker_files:
            try:
                repository_name = docker.build(docker_file, tag)
                click.secho('Container "{}" built from dockerfile "{}"\n'.format(repository_name,
                                                                                 docker_file), fg='green')
            except IndexError:
                pass
    except NotADockerProjectException:
        logger.error("Not a docker project")
        sys.exit(1)
    except DockerException as e:
        click.secho(
            'Failed to run docker command with message "{message}", exit code: {errno}'.format(
                message=e.message,
                errno=e.errno
            ), fg="red"
        )
        sys.exit(1)


@cli.command(help='Push docker image')
@click.option('--ask', is_flag=True, help='Ask which repository to push')
@click.option('--force-stage', is_flag=True, default=False,
              help='Add stage to repository name even if --subproject has been specified')
@click.option('--subproject', default=None, help='Push given subproject')
@stylist_context
def push(ctx, ask, subproject, force_stage):
    """
    @type ctx: stylist.cli.Context
    @type ask: str

    @@ignore_check@@
    """
    click.secho('Pushing docker container', fg='blue')

    docker_files = _get_docker_files(ctx, ask, subproject)

    try:
        docker = Docker(ctx, subproject, force_stage)
        for docker_file in docker_files:
            try:
                repository_name = docker.push(docker_file)
                click.secho(
                    'Image for container "{}" pushed from dockerfile "{}"\n'.format(repository_name, docker_file),
                    fg='green'
                )
            except IndexError:
                pass
    except NotADockerProjectException:
        sys.exit(1)
    except DockerException as e:
        click.secho(
            'Failed to run docker command with message "{message}", exit code: {errno}'.format(
                message=e.message,
                errno=e.errno
            ), fg="red"
        )
        sys.exit(1)


@cli.command(help='List current project images')
@click.option('--subproject', default=None, help='List images for given subproject')
@stylist_context
def images(ctx, subproject):
    """
    @type ctx: stylist.cli.Context
    """
    try:
        docker_files = _get_docker_files(ctx, False, subproject)

        docker = Docker(ctx, subproject, False)
        docker.images(docker_files[0])
    except NotADockerProjectException:
        sys.exit(1)


def _ask_about_docker_files(message, docker_files):
    click.secho(message, fg='blue')
    for i, docker_file in enumerate(docker_files):
        click.secho('  [{}] {}'.format(i + 1, docker_file), fg='blue')
    all_above = len(docker_files) + 1
    click.secho('  [{}] All above.'.format(all_above), fg='blue')

    docker_index = click.prompt(click.style('Build', fg='blue'), default=all_above)
    if docker_index == all_above:
        docker_files_indexes = tuple(range(0, len(docker_files)))
    else:
        docker_files_indexes = (docker_index - 1,)

    return docker_files_indexes


def _get_docker_files(ctx, ask, subproject):
    path = join(ctx.working_dir, subproject) if subproject else ctx.working_dir
    docker_files = glob.glob('{}/Dockerfile*'.format(path))

    if ask:
        return _ask_about_docker_files('Which docker file would you like to build?', docker_files)
    else:
        return docker_files
