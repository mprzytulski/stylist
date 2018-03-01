from copy import copy

import click

from stylist.cli import logger
from stylist.commands import cli_prototype
from stylist.wrapper.chalice import Chalice, ChaliceException

cli = copy(cli_prototype)
cli.short_help = "Helper for AWS chalice framework"


@cli.command(help="Deploy chalice project")
@click.argument('chalice_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def deploy(ctx, chalice_args):
    try:
        apex = Chalice(ctx)
        apex.deploy(chalice_args)
    except ChaliceException as e:
        logger.error(e.message)
        logger.error(e.cmd)
