from datetime import datetime
from os.path import join, basename

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
            docker.tag(build_tag, ':'.join([name, tag]))


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
    repository_provider = stylist.docker_repository_provider()

    with stylist.features.docker(path) as docker:
        for name, dockerfile in docker.list_containers().items():
            repository_provider.create_repository(name, ignore_if_exists=True)
            repository = repository_provider.get_repository(name)
            tags = docker.push(name, repository, tag)
            click.secho("Pushed: \n" + ("\n".join(tags)), fg='blue')


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


@cli.command(
    help='Run command in project docker container with AWS settings for given stage',
    context_settings=dict(ignore_unknown_options=True)
)
@click.option('--tag', default='latest', help='Run given tag')
@click.option('--non-interactive', default=False, is_flag=True, help='Execute command in non interactive mode')
@click.option('--subproject', default=None, help='Run subproject container')
@click.option('--container', default=None, help='Entern named container')
@click.argument('cmd', default='/bin/bash')
@click.argument('docker_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def enter(stylist, subproject, tag, non_interactive, cmd, docker_args, container):
    path = join(stylist.working_dir, subproject) if subproject else stylist.working_dir

    with stylist.features.docker(path) as docker:
        containers = docker.list_containers()
        if not container and len(containers) > 1:
            click.secho('Project contains more than one container, please select one to run')
            selection = click.prompt(
                "Please select container\n" + "\n".join(
                    [
                        '{}. {} ({})'.format(idx, container[0], basename(container[1]))
                        for idx, container in enumerate(iter(containers.items()), 1)
                    ]
                ) + "\n Enter container number: ",
                type=click.Choice(map(lambda x: str(x), range(1, len(containers.keys()) + 1)))
            )
            container = containers.items()[int(selection) - 1]
        else:
            container = next(iter(containers.items()))

        for message in docker.enter(container[0] + ':' + tag, container[1], not non_interactive, cmd, docker_args, True):
            click.echo(message)







