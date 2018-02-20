import os
from copy import copy

import click
import sys
from click import style
from stylist.cli import stylist_context, logger
from stylist.click.types import Boolean
from stylist.commands import cli_prototype
from stylist.feature import Templates
from stylist.wrapper.terraform import Terraform, TerraformException
from stylist.utils import colourize

cli = copy(cli_prototype)
cli.short_help = 'Wrapper around terraform'


@cli.command(help="Show terraform plan for current env")
@click.option('--force-update', is_flag=True, default=False, help="Force modules update, by default modules are updated after an hour")
@stylist_context
def plan(ctx, force_update):
    """
    @type ctx: stylist.cli.Context
    """
    try:
        terraform = Terraform(ctx)
        plan, exit_code = terraform.plan(force_update=force_update)
        sys.exit(exit_code)
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
        plan_path, exit_code = terraform.plan(True)

        if exit_code != 0:
            return exit_code

        _apply = click.prompt(
            style('Apply saved plan to "{}"? '.format(colourize(ctx.environment)), fg="green"),
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
@click.argument("module_name")
@click.argument("alias")
@stylist_context
def configure_module(ctx, module_name, alias):
    templates = Templates(ctx)

    terraform = Terraform(ctx, templates)
    terraform.configure_module(module_name, alias)


@cli.command(name="list-modules", help="List available terraform modules")
@stylist_context
def configure_module(ctx):
    templates = Templates(ctx)

    terraform = Terraform(ctx, templates)
    terraform.list_modules()
