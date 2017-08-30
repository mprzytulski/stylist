import click
import sys

from stylist.cli import logger
from stylist.lib.utils import table


def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


@click.command()
def cli():
    """
    Verify installation and configuration of required tools
    :return:
    """
    tools = ("aws", "terraform", "serverless", "virtualenv", "pip")

    software = []

    has_errors = False
    for tool in tools:
        path = which(tool)
        c = "white"
        if path is None:
            has_errors = True
            c = "red"

        software.append([click.style(tool, fg=c), click.style(path or "-", fg=c)])

    click.secho(
        table("SYSTEM CHECK", software, ["TOOL", "STATUS"]).table
    )

    sys.exit(0 if not has_errors else 1)
