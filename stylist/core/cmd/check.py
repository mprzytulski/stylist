import os
import sys

import click

from stylist.lib import which
from stylist.utils import table


@click.command()
def cli():
    """
    Verify installation and configuration of required tools
    :return:
    """
    tools = ("aws", "terraform", "serverless", "virtualenv", "pip", "aws-vault", "yoyo-migrate", "chalice")

    software = []

    has_errors = False
    for tool in tools:
        path = which(tool)
        c = "white"
        if not path:
            has_errors = True
            c = "red"

        software.append([click.style(tool, fg=c), click.style(path or "-", fg=c)])

    click.secho(
        table("SYSTEM CHECK", software, ["TOOL", "STATUS"]).table
    )

    sys.exit(0 if not has_errors else 1)
