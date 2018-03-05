import re
import sys
from datetime import datetime

import click

from stylist.cli import logger
from stylist.commands import GroupPrototype
from stylist.utils import table
from stylist.wrapper.docker import Docker, NotADockerProjectException, DockerException, _get_docker_files

cli = GroupPrototype.create('Docker image helper')


@cli.command(help='Build docker image using Dockerfile', context_settings=dict(
    ignore_unknown_options=True,
))
@click.option('--tag', default=datetime.now().strftime('%Y%m%d_%H%M'))
@click.option('--ask', is_flag=True, help='Ask which repository to build')
@click.option('--subproject', default=None, help='Build docker image located in named subdirectory / project')
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
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
@click.pass_obj
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
@click.pass_obj
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
        logger.error("Unable to locate Docker file - is that a Docker project?")
        sys.exit(1)


@cli.command(help='Run command in project docker container with AWS settings for given stage')
@click.option('--tag', default='latest', help='Run given tag')
@click.option('--non-interactive', default=False, is_flag=True, help='Execute command in non interactive mode')
@click.option('--subproject', default=None, help='Run subproject container')
@click.argument('cmd', default='/bin/bash')
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def enter(ctx, subproject, tag, non_interactive, cmd, docker_args):
    try:
        docker = Docker(ctx, subproject)
        args = ['run', '--rm', '-p', '8000:8000', '-v', '{}:/app'.format(ctx.working_dir)] + list(docker_args)

        if not non_interactive:
            args.append('-it')

        for k, v in ctx.provider.credentials.items():
            args += ['-e', '{}={}'.format(k, v)]

        args.append('{}:{}'.format(re.sub('\W', '-', ctx.name), tag or 'latest'))
        args.append(cmd)

        docker.run_docker(args)
    except NotADockerProjectException as e:
        logger.error("Unable to locate Docker file - is that a Docker project?")
        sys.exit(1)
    except DockerException as e:
        # Exit from the container
        if e.errno == 130:
            sys.exit(130)
        click.secho(
            "Failed to run docker command with message '{message}', exit code: {errno}\nCommand: {cmd}".format(
                message=e.message,
                errno=e.errno,
                cmd=' '.join(e.cmd)
            ), fg="red"
        )
        sys.exit(1)
