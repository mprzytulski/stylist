from os.path import isdir, join

import click

from stylist.cli import logger
# from stylist.provider.aws import SSM
# from stylist.utils import colourize
# from stylist.wrapper.terraform import Terraform, TerraformException
from stylist.core.click import GroupPrototype

cli = GroupPrototype.create('Manage project environments')


@cli.command(help="Show active environment for current working directory")
@click.pass_obj
def selected(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.secho(
        colourize(ctx.environment)
    )


@cli.command(help="Activate named profile")
@click.argument("name")
@click.pass_obj
def select(ctx, name, project_name=None, profile=None, working_dir=None):
    """
    @type ctx: stylist.cli.Context
    """
    with open(ctx.environment_file, 'w') as f:
        f.write(name)

    # @todo: check if there is a aws profile matching given env, if not - call create action

    click.secho("Selected profile: {}".format(colourize(name)))


@cli.command(name="list", help="List all available profiles")
@click.pass_obj
def list_profiles(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    click.echo("All defined environments:")

    for f in ctx.settings.get('stylist', {}).get('stages', []):
        click.secho(
            ("-> " if f == ctx.environment else "   ") + colourize(f)
        )
