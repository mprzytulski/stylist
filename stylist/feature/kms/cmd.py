import click

from stylist.core.click import GroupPrototype
from stylist.utils import table

cli = GroupPrototype.create("AWS KMS encryption helper")


@cli.command(name="list-keys", help="List KMS aliases")
@click.pass_obj
def list_keys(stylist):
    kms = stylist.containers.get('aws').kms()

    click.secho(
        table(
            "KMS ALIASES",
            map(lambda x: x.values(), kms.list_aliases()),
            ["ARN", "NAME", "KeyId"]
        ).table
    )


@cli.command(help="Encrypt plain text with context encryption key")
@click.argument("plain_text")
@click.option("--key-alias", help="Use given key alias instead of configured / default one.")
@click.option("--plain", default=False, flag_value='plain', help="Return encrypted value only")
@click.pass_obj
def encrypt(stylist, plain_text, plain, key_alias=None):
    kms = stylist.containers.get('aws').kms()
    encrypted, key_id = kms.encrypt(plain_text, key_alias)

    if plain:
        click.echo(encrypted)
    else:
        click.echo("Used key: {}".format(key_id))
        click.secho(
            'Encrypted value: "{}"'.format(encrypted)
        )


@cli.command(help="Encrypt plain text with context encryption key")
@click.argument("encrypted")
@click.pass_obj
def decrypt(stylist, encrypted):
    kms = stylist.containers.get('aws').kms()
    decrypted = kms.decrypt(encrypted)

    click.echo(decrypted)
