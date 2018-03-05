import base64

import click

from stylist.cli import logger
from stylist.commands import GroupPrototype
from stylist.utils import line_prefix

cli = GroupPrototype.create("AWS KMS encryption helper")


@cli.command(help="Encrypt plain text with context encryption key")
@click.argument("plain_text")
@click.option("--plain", default=False, flag_value='plain', help="Return encrypted value only")
@click.pass_obj
def encrypt(ctx, plain_text, plain):
    kms = ctx.provider.session.client("kms")

    key_id = ctx.provider.ssm.get_encryption_key().get('TargetKeyId')

    response = kms.encrypt(
        KeyId=key_id,
        Plaintext=bytes(plain_text),
    )

    encrypted = base64.b64encode(response.get("CiphertextBlob"))

    if plain:
        click.echo(encrypted)
    else:
        click.secho(
            line_prefix(ctx) + ' ({}) '.format(key_id) + encrypted
        )


@cli.command(help="Encrypt plain text with context encryption key")
@click.argument("encrypted")
@click.option("--plain", default=False, flag_value='plain', help="Return decrypted value only")
@click.pass_obj
def decrypt(ctx, encrypted, plain):
    kms = ctx.provider.session.client("kms")

    try:
        decrypted = kms.decrypt(
            CiphertextBlob=base64.b64decode(encrypted)
        ).get('Plaintext').decode("utf-8")

        if plain:
            click.echo(decrypted)
        else:
            click.secho(
                line_prefix(ctx) + decrypted
            )
    except Exception, e:
        logger.error(e.message)
        return 1
