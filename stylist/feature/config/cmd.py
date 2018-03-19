import click

from stylist.click.types import Boolean
from stylist.core.click import GroupPrototype
from stylist.feature.config.lib import resolve_full_name, FORMATTER
from stylist.utils import table

cli = GroupPrototype.create("Manage project configuration")


def resolve_namespaces(stylist, namespace):
    return map(
        resolve_full_name,
        (namespace or (stylist.service_name,))
    )


@cli.command(name="write", help="Write / create new parameter under given name")
@click.option('--namespace', help="Namespace under which parameter should be stored, for example service:name")
@click.option('--encrypt/--no-encrypt', help="Encrypt value", default=True)
@click.argument('parameter')
@click.argument('value')
@click.pass_obj
def config_write(stylist, namespace, encrypt, parameter, value):
    with stylist.config_provider() as cp:
        storage_name = cp.write(
            resolve_full_name(namespace or stylist.service_name, parameter),
            value,
            encrypt
        )

    click.secho("Value: '{}' has been stored under: '{}'".format(value, storage_name))


@cli.command(help="Delete parameter with given name")
@click.option('--namespace', help="Namespace under which parameter should be stored, for example service:name")
@click.argument('parameter')
@click.pass_obj
def delete(stylist, namespace, parameter):
    full_name = resolve_full_name(namespace or stylist.service_name, parameter)

    if not click.prompt(click.style('Delete "{}" parameter?', fg='red').format(full_name), type=Boolean(),
                        default=False):
        click.secho('Aborted', fg='yellow')
        return 1

    with stylist.config_provider() as cp:
        cp.delete(full_name)

    click.secho("Parameter '{}' has been deleted.".format(full_name), fg='green')


@cli.command(name="list", help="List all parameters for given service / resource")
@click.option("--format", help="Name output format", type=click.Choice(['full', 'env', 'short']), default="full")
@click.argument("namespace", nargs=-1)
@click.pass_obj
def config_list(stylist, namespace, format):
    with stylist.config_provider() as cp:
        parameters = cp.describe_parameters(
            *resolve_namespaces(stylist, namespace)
        )

    click.secho(
        table(
            "KNOWN PARAMETERS",
            map(FORMATTER.get(format), parameters.values()),
            ["NAME", "TYPE", "VALUE", "LAST MODIFIED", "LAST MODIFIED BY"]
        ).table
    )


@cli.command(name="dump", help="Dump all parameters in key=value format")
@click.argument("namespace", nargs=-1)
@click.pass_obj
def config_dump(stylist, namespace):
    with stylist.config_provider() as cp:
        parameters = cp.get_parameters(
            *resolve_namespaces(stylist, namespace)
        )

    formatter = FORMATTER.get('env')
    for name, value in parameters.items():
        click.echo("{}={}".format(formatter(name), value))
