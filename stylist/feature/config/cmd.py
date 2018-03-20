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


@cli.command(name="sync", help="Synchronise configuration variables between profiles")
@click.option("--namespaces", help="Namespaces to migrate", multiple=True)
@click.argument("source")
@click.argument("destination")
@click.pass_obj
def sync_vars(ctx, namespaces, source, destination):
    pass
    # @todo: implement new logic

    # try:
    #     profiles = ctx.settings.get('stylist', {}).get('stages')
    #     if source not in profiles:
    #         raise Exception('Source profile "{}" is missing'.format(source))
    #
    #     if destination not in profiles:
    #         raise Exception('Destination profile "{}" is missing'.format(destination))
    #
    #     click.secho("Migrating terraform variables", fg="blue")
    #
    #     if isdir(join(ctx.working_dir, 'terraform')):
    #         try:
    #             terraform = Terraform(ctx)
    #             terraform.sync_vars(source, destination)
    #         except TerraformException as e:
    #             click.secho("No stage tfvars. Skipping terraform migration.")
    #
    #     namespaces = list(namespaces)
    #     if not namespaces:
    #         namespaces.append('service:{}'.format(ctx.name))
    #
    #     click.secho("Migrating ssm namespaces", fg="blue")
    #     source_ssm = SSM(ctx.provider.get_session_for_stage(source).client('ssm'), ctx)
    #     destination_session = ctx.provider.get_session_for_stage(destination)
    #     destination_ssm = SSM(destination_session.client('ssm'), ctx)
    #
    #     for namespace in namespaces:
    #         click.secho("Migrating '{}' from '{}' -> '{}'".format(namespace, colourize(source), colourize(destination)))
    #         diff = SSM.sync_vars(source_ssm, destination_ssm, namespace)
    #
    #         for key, value in diff.items():
    #             destination_ssm.write(namespace, key, value, session=destination_session)
    #
    # except Exception as e:
    #     logger.error(e.message)
