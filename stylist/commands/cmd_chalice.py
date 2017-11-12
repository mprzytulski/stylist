import glob
import json
import os
from copy import copy

import click
import subprocess

from os.path import join, isfile, isdir

import shutil

import sys

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.wrapper.apex import Apex, ApexException
from stylist.wrapper.chalice import Chalice, ChaliceException
from stylist.wrapper.docker import Docker

cli = copy(cli_prototype)
cli.short_help = "Helper for AWS chalice framework"


@cli.command(help="Deploy chalice project")
@click.argument('chalice_args', nargs=-1, type=click.UNPROCESSED)
@stylist_context
def deploy(ctx, chalice_args):
    try:
        apex = Chalice(ctx)
        apex.deploy(chalice_args)
    except ChaliceException as e:
        logger.error(e.message)
        logger.error(e.cmd)


@cli.command(help="Init chalice project")
@click.argument('chalice_args', nargs=-1, type=click.UNPROCESSED)
@stylist_context
def init(ctx, chalice_args):
    try:
        if isdir(join(ctx.working_dir, ctx.name)):
            logger.error("Looks like there is a chalice project in current repository")
            sys.exit(1)

        apex = Chalice(ctx)
        apex.init(chalice_args)

        click.secho("All done.", fg="green")
    except ChaliceException as e:
        logger.error(e.message)
        logger.error(e.cmd)
