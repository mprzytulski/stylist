import subprocess

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.commands.cmd_check import which
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
