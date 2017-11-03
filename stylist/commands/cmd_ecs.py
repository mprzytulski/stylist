import sys
from copy import copy

import click
from click import style

from stylist.cli import stylist_context, logger
from stylist.click.types import Boolean
from stylist.commands import cli_prototype
from stylist.utils import colourize
from stylist.wrapper.docker import NotADockerProjectException, Docker, _get_docker_files
from stylist.wrapper.terraform import Terraform, TerraformException

cli = copy(cli_prototype)
cli.short_help = 'ECS Service management'


@cli.command(help='Enrol given version of docker image')
@click.option('--service', default=None, help='Overwrite service name')
@click.option('--tag', default='latest', help='Tag which should be enrolled')
@stylist_context
def enrol(ctx, service, tag):
    """
    @type ctx: stylist.cli.Context
    """
    service = service or ctx.name

    try:
        docker_files = _get_docker_files(ctx, False, None)

        docker = Docker(ctx, None)
        deploy_tag = tag if tag != 'latest' else docker.get_latest_build_tag(docker_files[0])

        terraform = Terraform(ctx)

        env_vars = terraform.get_env_vars()
        env_vars['ecs_service_{}_version'.format(service)] = deploy_tag

        terraform.dump_env_vars(env_vars)

        plan_path, exit_code = terraform.plan(True)

        if exit_code != 0:
            click.secho("")
            sys.exit(exit_code)

        msg = style('Enrol "{tag}" to "{env}" with given plan? '.format(
            tag=deploy_tag, env=colourize(ctx.environment)), fg="green"
        )

        if not click.prompt(msg, type=Boolean(), default=True):
            click.secho("Aborted!", fg="yellow")
            sys.exit(2)

        terraform.apply(plan_path)

        ecs = ctx.provider.session.client('ecs')
        task = ecs.list_task_definitions(familyPrefix=service, status='ACTIVE').get('taskDefinitionArns')[0]

        ecs.update_service(
            cluster='ecs-main-cluster',
            service=service,
            taskDefinition=task
        )

        click.secho("Version {} has been enrolled.".format(deploy_tag))
    except NotADockerProjectException:
        sys.exit(1)
    except TerraformException as e:
        logger.error(e.message)
        sys.exit(2)
