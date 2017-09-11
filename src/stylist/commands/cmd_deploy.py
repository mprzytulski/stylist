import os
import subprocess
import sys

import click
from click import style
from os.path import isdir, join

from stylist.cli import stylist_context
from stylist.click.types import Boolean
from stylist.wrapper.serverless import Serverless, InvalidContextException
from stylist.utils import colourize


@click.command(help="Deploy project")
@click.option("--non-interactive", default=False, flag_value='non_interactive', help="Run in non-interactive mode")
@stylist_context
def cli(ctx, non_interactive):
    if ctx.environment in ["local", "dev", "development", "test"]:
        click.secho(
            style("Can't deploy to '{env}' as it's not deployable stage".format(env=ctx.environment), fg="yellow")
        )
        sys.exit(2)

    go = True
    if not non_interactive:
        go = click.prompt(
            'Deploy to {stage}'.format(stage=colourize(ctx.environment)), type=Boolean(), default=False
        )

    if not go:
        click.secho("Aborted.", fg="yellow")
        sys.exit(1)

    # Deploy serverless project
    try:
        sls = Serverless.from_context(ctx)
        _deploy_serverless(ctx)
    except InvalidContextException:
        pass

    migration_dirs = [
        join(ctx.working_dir, 'migrations'),
        join(os.getcwd(), 'migrations')
    ]
    for _dir in [_dir for _dir in migration_dirs if isdir(_dir)]:
        _run_migrations(ctx, _dir)


def _deploy_serverless(ctx):
    args = ["serverless", "--stage", ctx.environment, "deploy"]

    click.secho("Execute: {cmd}".format(cmd=style(' '.join(args), fg="green")))

    p = subprocess.Popen(args, stdout=click.get_text_stream("stdout"),
                         stderr=click.get_text_stream("stderr"))

    out, err = p.communicate()


def _run_migrations(ctx, migrations_dir):
    pass


def _deploy_docker(ctx):
    pass
