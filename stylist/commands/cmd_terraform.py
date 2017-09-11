import os
from copy import copy

import click
from click import style
from stylist.cli import stylist_context, logger
from stylist.click.types import Boolean
from stylist.commands import cli_prototype
from stylist.feature import Templates
from stylist.wrapper.terraform import Terraform, TerraformException

cli = copy(cli_prototype)
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
            style("Apply saved plan? ", fg="green"),
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


@cli.command(name="configure-module", help="Configure terraform module")
@click.option("--templates-version", default="master",
              help="Git branch / tag of templates repository which should be used for init")
@click.argument("module_name")
@click.argument("alias")
@stylist_context
def configure_module(ctx, module_name, alias, templates_version):
    templates = Templates(templates_version)

    terraform = Terraform(ctx, templates)
    terraform.configure_module(module_name, alias)
