import os
import subprocess

import click

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.commands.cmd_check import which
from stylist.lib.click.types import Boolean
from stylist.lib.terraform import Terraform, TerraformException

cli = cli_prototype
cli.short_help = 'Wrapper around terraform'


@cli.command(help="Show terraform plan for current env")
@stylist_context
def plan(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    try:
        terraform = Terraform(ctx)
        terraform.plan()
    except TerraformException as e:
        logger.error(e.message)


@cli.command(help="Create terraform plan and apply")
@stylist_context
def apply(ctx):
    """
    @type ctx: stylist.cli.Context
    """
    plan_path = None
    try:
        terraform = Terraform(ctx)
        plan_path = terraform.plan(True)

        _apply = click.prompt(
            "Apply saved plan? ",
            type=Boolean(),
            default=True
        )

        if _apply:
            terraform.apply(plan_path)
        else:
            click.secho("Aborted.", fg="yellow")
    except TerraformException as e:
        logger.error(e.message)
    finally:
        if plan_path:
            os.remove(plan_path)
