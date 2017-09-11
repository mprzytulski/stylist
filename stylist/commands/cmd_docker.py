import sys
from copy import copy
from datetime import datetime
import click
from fs import open_fs
from stylist.cli import stylist_context
from stylist.commands import cli_prototype
from stylist.wrapper.docker import Docker, NotADockerProjectException, DockerException

cli = copy(cli_prototype)
cli.short_help = 'Docker image helper'


@cli.command(help="Build docker image using Dockerfile")
@click.option("--no-tag", default=False, flag_value='no_tag', help="Do not tag build")
@stylist_context
def build(ctx, no_tag):
    """
    @type ctx: stylist.cli.Context
    """
    try:
        build_tag = datetime.now().strftime('%Y%m%d_%H%M') if not no_tag else None

        click.secho('Building docker container', fg='blue')

        current_fs = open_fs(ctx.working_dir)
        docker_files = [p for p in current_fs.walk.files(filter=['Dockerfile*'])]

        if len(docker_files) > 1:
            click.secho('Which docker file would you like to build?', fg='blue')
            for i, docker_file in enumerate(docker_files):
                click.secho('  [{}] {}'.format(i+1, docker_file), fg='blue')
            all_above = len(docker_files)+1
            click.secho('  [{}] All above.'.format(all_above), fg='blue')

            docker_index = click.prompt(click.style('Build', fg='blue'), default=all_above)
            if docker_index == all_above:
                docker_files_indexes = tuple(range(0, len(docker_files)))
            else:
                docker_files_indexes = (docker_index-1,)
        else:
            docker_files_indexes = (0,)

        current_fs.close()

        docker = Docker(ctx)
        for index in docker_files_indexes:
            try:
                docker.build(docker_files[index], build_tag)

                click.secho('Container "{}" ready'.format(docker_files[index]), fg='green')
            except IndexError:
                pass

        if not no_tag:
            click.secho('Container tagged: {}'.format(build_tag), fg='green')

    except NotADockerProjectException:
        sys.exit(1)


@cli.command(help="Build docker image using Dockerfile")
@click.argument("build_tag", "Image tag which should be pushed to current repository")
@stylist_context
def push(ctx, build_tag):
    """
    @type ctx: stylist.cli.Context
    """
    try:
        docker = Docker(ctx)
        remote = docker.push(build_tag)

        click.secho("Image ready: {remote}".format(remote=remote), fg="green")
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


@cli.command(help="List current project images")
@stylist_context
def images(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    try:
        docker = Docker(ctx)
        docker.images()
    except NotADockerProjectException:
        sys.exit(1)
