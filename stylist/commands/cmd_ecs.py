import sys
from copy import copy

import click
import re
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
@click.option('--tag', default='latest', help='Tag which should be enrolled')
@click.option('--subproject', help='Tag which should be enrolled')
@stylist_context
def enrol(ctx, subproject, tag):
    """
    @type ctx: stylist.cli.Context
    """
    try:
        docker_files = _get_docker_files(ctx, False, subproject)
        service = subproject or ctx.name

        if not docker_files:
            logger.error("Unable to locate Dockerfile for given project")
            sys.exit(1)

        # @todo check if remote image exists before enrolling service
        docker = Docker(ctx, subproject)
        deploy_tag = tag if tag != 'latest' else docker.get_latest_build_tag(docker_files[0])

        terraform = Terraform(ctx)

        env_vars = terraform.get_env_vars()
        env_vars[
            'ecs_service_{}_version'.format(
                docker.get_repository_name(docker_files[0]).replace('/', '_')
            )
        ] = deploy_tag

        terraform.dump_env_vars(env_vars)

        plan_path, exit_code = terraform.plan(True)
        if exit_code != 0:
            click.secho('terraform plan failed')
            sys.exit(exit_code)

        msg = style('Enrol "{tag}" to "{env}" with given plan? '.format(
            tag=deploy_tag, env=colourize(ctx.environment)), fg="green"
        )

        if not click.prompt(msg, type=Boolean(), default=True):
            click.secho("Aborted!", fg="yellow")
            sys.exit(2)

        exit_code = terraform.apply(plan_path)
        if exit_code != 0:
            click.secho('terraform apply failed')
            sys.exit(exit_code)

        task_name = str(re.sub("\W", "-", service))
        ecs = ctx.provider.session.client('ecs')
        tasks = ecs.list_task_definitions(familyPrefix=task_name, status='ACTIVE')

        if not tasks.get('taskDefinitionArns'):
            logger.error("Opss. Unable to locate task definition")
            return

        ecs.update_service(
            cluster='ecs-main-cluster',
            service=task_name,
            taskDefinition=tasks.get('taskDefinitionArns')[-1]
        )

        click.secho("Version {} has been enrolled.".format(deploy_tag))
    except NotADockerProjectException:
        sys.exit(1)
    except TerraformException as e:
        logger.error(e.message)
        sys.exit(2)
