import click

from stylist.core.click import GroupPrototype
from stylist.utils import colourize


def get_main_group():
    return selected


cli = GroupPrototype.create('Manage project environments', invoke_without_command=get_main_group)


@cli.command(help="Show active environment for current working directory")
@click.pass_obj
def selected(stylist, **kwargs):
    """
    @type ctx: stylist.core.Stylist
    """
    click.secho(
        colourize(stylist.profile)
    )


@cli.command(name="set", help="Activate named profile")
@click.argument("name")
@click.pass_obj
def select(stylist, name, **kwargs):
    """
    @type stylist: stylist.core.Stylist
    """
    with open(stylist.environment_file, 'w') as f:
        f.write(name)

    click.secho("Selected profile: {}".format(colourize(name)))


@cli.command(name="list", help="List all available profiles")
@click.pass_obj
def list_profiles(ctx):
    """
    @type ctx: stylist.core.Stylist
    """
    click.echo("All defined environments:")

    for f in ctx.settings.get('stylist', {}).get('stages', []):
        click.secho(
            ("-> " if f == ctx.environment else "   ") + colourize(f)
        )
