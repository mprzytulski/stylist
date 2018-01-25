import re
import sys
from copy import copy

import click

from stylist.cli import stylist_context, logger
from stylist.click.types import Boolean
from stylist.commands import cli_prototype
from stylist.utils import table

cli = copy(cli_prototype)
cli.short_help = "Manage SSM parameters store"


def write_helper(ctx, namespace, encrypt, parameter, value):
    try:
        namespace = namespace or "service:" + re.sub('\W', '-', ctx.name)

        ctx.set_provider(ctx.environment)
        full_name = ctx.provider.ssm.write(namespace.lower(), parameter.lower(), value, encrypt)
    except Exception as e:
        logger.error(e.message)
        sys.exit(1)

    click.secho("Stored '{}' under key: '{}'".format(value, full_name), fg='green')


@cli.command(help="Write / create new parameter under SSM")
@click.option('--namespace', help="Namespace under which parameter should be stored, for example service:name")
@click.option('--encrypt/--no-encrypt', help="Encrypt value", default=True)
@click.argument('parameter')
@click.argument('value')
@stylist_context
def write(ctx, namespace, encrypt, parameter, value):
    write_helper(ctx, namespace, encrypt, parameter, value)


@cli.command(help="List all parameters for given service / resource SSM")
@click.argument("namespace", nargs=-1)
@stylist_context
def list(ctx, namespace):
    namespace = namespace or ("service:" + re.sub('\W', '-', ctx.name),)

    click.secho(
        table(
            "KNOWN PARAMETERS",
            ctx.provider.ssm.get_full_parameters(*namespace),
            ["NAME", "TYPE", "VALUE", "LAST MODIFIED", "LAST MODIFIED BY"]
        ).table
    )


@cli.command(help="Dump all parameters in key=value format")
@click.argument("namespace", nargs=-1)
@stylist_context
def dump(ctx, namespace):
    namespace = namespace or ("service:" + re.sub('\W', '-', ctx.name),)
    _all = ctx.provider.ssm.get_full_parameters(*namespace, env=True)

    for param in _all:
        click.echo("{}={}".format(param[0], param[2]))


@cli.command(help="Delete parameter with given name")
@click.option('--namespace', help="Namespace under which parameter should be stored, for example service:name")
@click.argument('parameter')
@stylist_context
def delete(ctx, namespace, parameter):
    namespace = namespace or "service:" + re.sub('\W', '-', ctx.name)

    ssm = ctx.provider.ssm
    full_name = ssm.get_full_name(*namespace.split(':'), parameter=parameter)

    if not click.prompt(click.style('Delete "{}" parameter?', fg='red').format(full_name), type=Boolean(),
                        default=False):
        click.secho('Aborted', fg='yellow')
        sys.exit(1)

    try:
        ssm.delete(namespace, parameter)
    except Exception as e:
        click.secho('Error deleting parameter: {}'.format(e.message), fg='yellow')
        sys.exit(2)

    click.secho('Deleted', fg='green')
