import sys
import glob
from copy import copy
from datetime import datetime
from os.path import join

import click
from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.utils import table
from stylist.wrapper.docker import Docker, NotADockerProjectException, DockerException, _get_docker_files

cli = copy(cli_prototype)
cli.short_help = 'Docker image helper'


@cli.command(help='Build docker image using Dockerfile', context_settings=dict(
    ignore_unknown_options=True,
))
@click.option('--tag', default=datetime.now().strftime('%Y%m%d_%H%M'))
@click.option('--ask', is_flag=True, help='Ask which repository to build')
@click.option('--subproject', default=None, help='Build docker image located in named subdirectory / project')
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
@stylist_context
def build(ctx, tag, ask, subproject, profile=None, project_name=None, working_dir=None, docker_args=None):
    """
    @type ctx: stylist.cli.Context
    @type tag: string
    @type ask: string

    @@ignore_check@@
    """
    click.secho('Building docker container', fg='blue')

    docker_files = _get_docker_files(ctx, ask, subproject)
    try:
        docker = Docker(ctx, subproject)
        for docker_file in docker_files:
            try:
                repository_name = docker.build(docker_file, tag, docker_args)
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
@click.option('--tag', default='latest', help='Push given tag')
@click.option('--subproject', default=None, help='Push given subproject')
@click.option('--force-build', default=False, is_flag=True, help='Force build before push')
@stylist_context
def push(ctx, ask, subproject, force_build, tag):
    """
    @type ctx: stylist.cli.Context
    @type ask: str

    @@ignore_check@@
    """

    if force_build:
        click.get_current_context().invoke(
            build,
            ask=ask,
            tag=datetime.now().strftime('%Y%m%d_%H%M'),
            subproject=subproject
        )

    click.secho('Pushing docker container', fg='blue')

    docker_files = _get_docker_files(ctx, ask, subproject)

    try:
        docker = Docker(ctx, subproject)
        for docker_file in docker_files:
            try:
                for name in docker.push(docker_file, tag):
                    click.secho(
                        'Image for container "{}" pushed from dockerfile "{}"\n'.format(name, docker_file),
                        fg='green'
                    )
            except IndexError:
                pass
    except NotADockerProjectException:
        sys.exit(1)
    except DockerException as e:
        click.secho(
            "Failed to run docker command with message '{message}', exit code: {errno}\nCommand: {cmd}".format(
                message=e.message,
                errno=e.errno,
                cmd=' '.join(e.cmd)
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

        docker = Docker(ctx, subproject)

        images_list = []
        for image in docker.images(docker_files[0]):
            images_list.append([
                image.get('ID'),
                image.get('Repository'),
                image.get('Tag'),
                image.get('VirtualSize'),
                image.get('CreatedAt')]
            )

        click.secho(
            table(
                "DOCKER IMAGES",
                images_list,
                ["ID", "Repository", "Tag", "Size", "Created"]
            ).table
        )

    except NotADockerProjectException:
        sys.exit(1)
