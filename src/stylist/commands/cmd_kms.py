import base64

import click

from stylist.cli import stylist_context
from stylist.commands import cli_prototype
from stylist.lib.utils import colourize

cli = cli_prototype
cli.short_help = "AWS KMS encryption helper"


@cli.command(help="Encrypt plain text with context encryption key")
@click.argument("plain_text")
@click.option("--plain", default=False, flag_value='plain', help="Return encrypted value only")
@stylist_context
def encrypt(ctx, plain_text, plain):
    kms = ctx.provider.session.client("kms")

    response = kms.encrypt(
        KeyId=ctx.provider.kms_key,
        Plaintext=bytes(plain_text),
    )

    encrypted = base64.b64encode(response.get("CiphertextBlob"))

    if plain:
        click.echo(encrypted)
    else:
        click.secho(
            "[" + colourize(ctx.environment) + "@" + ctx.provider.profile + "] Decrypted: " +
            encrypted
        )


@cli.command(help="Encrypt plain text with context encryption key")
@click.argument("encrypted")
@click.option("--plain", default=False, flag_value='plain', help="Return decrypted value only")
@stylist_context
def decrypt(ctx, encrypted, plain):
    kms = ctx.provider.session.client("kms")

    decrypted = kms.decrypt(
        CiphertextBlob=base64.b64decode(encrypted)
    ).get('Plaintext').decode("utf-8")

    if plain:
        click.echo(decrypted)
    else:
        click.secho(
            "[" + colourize(ctx.environment) + "@" + ctx.provider.profile + "] Decrypted: " +
            decrypted
        )
