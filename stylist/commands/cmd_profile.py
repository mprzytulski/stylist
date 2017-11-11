from copy import copy
from os.path import isdir, join

import click

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.provider.aws import SSM
from stylist.utils import colourize
from stylist.wrapper.terraform import Terraform, TerraformException

cli = copy(cli_prototype)
cli.short_help = 'Manage project environments'


@cli.command(help="Show active environment for current working directory")
@stylist_context
def selected(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.secho(
        colourize(ctx.environment)
    )


@cli.command(help="Activate named profile")
@click.argument("name")
@stylist_context
def select(ctx, name, project_name=None, profile=None, working_dir=None):
    """
    @type ctx: stylist.cli.Context
    """
    with open(ctx.environment_file, 'w') as f:
        f.write(name)

    # @todo: check if there is a aws profile matching given env, if not - call create action

    click.secho("Selected profile: {}".format(colourize(name)))


@cli.command(name="list", help="List all available profiles")
@stylist_context
def list_profiles(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.echo("All defined environments:")

    for f in ctx.settings.get('stages', []):
        click.secho(
            ("-> " if f == ctx.environment else "   ") + colourize(f)
        )


@cli.command(name="sync-vars", help="Synchronise configuration variables between profiles")
@click.option("--namespaces", help="SSM namespaces to migrate", multiple=True)
@click.argument("source")
@click.argument("destination")
@stylist_context
def sync_vars(ctx, namespaces, source, destination):
    try:
        profiles = ctx.settings.get('stages')
        if source not in profiles:
            raise Exception('Source profile "{}" is missing'.format(source))

        if destination not in profiles:
            raise Exception('Destination profile "{}" is missing'.format(destination))

        click.secho("Migrating terraform variables", fg="blue")

        if isdir(join(ctx.working_dir, 'terraform')):
            try:
                terraform = Terraform(ctx)
                terraform.sync_vars(source, destination)
            except TerraformException as e:
                click.secho("No stage tfvars. Skipping terraform migration.")

        namespaces = list(namespaces)
        if not namespaces:
            namespaces.append('service:{}'.format(ctx.name))

        click.secho("Migrating ssm namespaces", fg="blue")
        source_ssm = SSM(ctx.provider.get_session_for_stage(source).client('ssm'), ctx)
        destination_session = ctx.provider.get_session_for_stage(destination)
        destination_ssm = SSM(destination_session.client('ssm'), ctx)

        for namespace in namespaces:
            click.secho("Migrating '{}' from '{}' -> '{}'".format(namespace, colourize(source), colourize(destination)))
            diff = SSM.sync_vars(source_ssm, destination_ssm, namespace)

            for key, value in diff.items():
                destination_ssm.write(namespace, key, value, session=destination_session)

    except Exception as e:
        logger.error(e.message)
