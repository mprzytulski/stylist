from datetime import datetime
from os.path import join

import click

from stylist.core.click import GroupPrototype
from stylist.utils import table

cli = GroupPrototype.create('Docker image helper')


@cli.command(help='Build docker image using Dockerfile', context_settings=dict(ignore_unknown_options=True))
@click.option('--tag', default=datetime.now().strftime('%Y%m%d_%H%M'))
@click.option('--subproject', default=None, help='Build docker image located in named subdirectory / project')
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def build(stylist, tag, subproject, docker_args=None):
    """
    @type stylist: stylist.core.Stylist
    @type tag: string
    @type subproject: string
    @type docker_args: list
    """
    path = join(stylist.working_dir, subproject) if subproject else stylist.working_dir

    click.secho('Building docker containers', fg='blue')
    with stylist.features.docker(path) as docker:
        for name, dockerfile in docker.list_containers().items():
            click.secho('Building container: {}'.format(name), fg='blue')
            build_tag = docker.build(name, dockerfile, docker_args)
            click.secho('Tagging container: {} with {}'.format(build_tag, ':'.join([name, tag])), fg='blue')
            docker.tag(build_tag, tag)


@cli.command(help='Push docker containers to remote repository')
@click.option('--tag', default='latest', help='Push given tag')
@click.option('--subproject', default=None, help='Push given subproject')
@click.pass_obj
def push(stylist, subproject, tag):
    """
    @type stylist: stylist.core.Stylist
    @type subproject: string
    """
    path = join(stylist.working_dir, subproject) if subproject else stylist.working_dir

    click.secho('Pushing docker containers', fg='blue')
    with stylist.features.docker(path) as docker:
        for name, dockerfile in docker.list_containers().items():
            pass
            # docker


@cli.command(help='List project containers')
@click.option('--subproject', default=None, help='Push given subproject')
@click.pass_obj
def containers(stylist, subproject):
    """
    @type stylist: stylist.core.Stylist
    @type subproject: string
    """
    path = join(stylist.working_dir, subproject) if subproject else stylist.working_dir

    with stylist.features.docker(path) as docker:
        click.secho(
            table(
                "DOCKER CONTAINERS",
                docker.list_containers(),
                ["Container", "Dockerfile"]
            ).table
        )


#
# try:
#     docker = Docker(ctx, subproject)
#     for docker_file in docker_files:
#         try:
#             for name in docker.push(docker_file, tag):
#                 click.secho(
#                     'Image for container "{}" pushed from dockerfile "{}"\n'.format(name, docker_file),
#                     fg='green'
#                 )


@cli.command(help='List current project images')
@click.option('--subproject', default=None, help='List images for given subproject')
@click.pass_obj
def images(stylist, subproject):
    """
    @type stylist: stylist.core.Stylist
    """
    path = join(stylist.working_dir, subproject) if subproject else stylist.working_dir

    with stylist.features.docker(path) as docker:
        for name, dockerfile in docker.list_containers().items():
            click.secho(
                table(
                    "DOCKER IMAGES: {}".format(name),
                    docker.images(name),
                    ["ID", "Container", "Tag", "Size", "Created"]
                ).table
            )

# @cli.command(help='Run command in project docker container with AWS settings for given stage')
# @click.option('--tag', default='latest', help='Run given tag')
# @click.option('--non-interactive', default=False, is_flag=True, help='Execute command in non interactive mode')
# @click.option('--subproject', default=None, help='Run subproject container')
# @click.argument('cmd', default='/bin/bash')
# @click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
# @click.pass_obj
# def enter(ctx, subproject, tag, non_interactive, cmd, docker_args):
#     pass
# try:
#     docker = Docker(ctx, subproject)
#     args = ['run', '--rm', '-p', '8000:8000', '-v', '{}:/app'.format(ctx.working_dir)] + list(docker_args)
#
#     if not non_interactive:
#         args.append('-it')
#
#     for k, v in ctx.provider.credentials.items():
#         args += ['-e', '{}={}'.format(k, v)]
#
#     args.append('{}:{}'.format(re.sub('\W', '-', ctx.name), tag or 'latest'))
#     args.append(cmd)
#
#     docker.run_docker(args)
# except NotADockerProjectException as e:
#     logger.error("Unable to locate Docker file - is that a Docker project?")
#     sys.exit(1)
# except DockerException as e:
#     # Exit from the container
#     if e.errno == 130:
#         sys.exit(130)
#     click.secho(
#         "Failed to run docker command with message '{message}', exit code: {errno}\nCommand: {cmd}".format(
#             message=e.message,
#             errno=e.errno,
#             cmd=' '.join(e.cmd)
#         ), fg="red"
#     )
#     sys.exit(1)
