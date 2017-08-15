import sys
from os.path import join, isfile

import click

from stylist import Env
from stylist.cli import Context, GroupWithCommandOptions, pass_context, logger
from stylist.commands import global_options, ensure_project_directory, NotProjectDirectoryException
from stylist.lib.serverless import Serverless


class LambdaFunction(Env, Context):
    def __init__(self, name):
        super(LambdaFunction, self).__init__(name)


@click.group(cls=GroupWithCommandOptions, short_help='Manage serverless lambda functions')
@global_options
@pass_context
def cli(ctx, working_dir):
    if working_dir is not None:
        try:
            ensure_project_directory(working_dir)
            ctx.working_dir = working_dir
        except NotProjectDirectoryException as e:
            logger.error(e.message)
            sys.exit(1)


@cli.command(help="Invoke serverless lambda function with predefined event")
@click.option("--mode", "-m", type=click.Choice(['sns', 'api-gw', 'direct']), default="direct", help="Execution mode")
@click.argument("function")
@click.argument("source", type=click.File(mode="r"))
@pass_context
def invoke(ctx, function, source, mode):
    sls_config = join(ctx.working_dir, "serverless.yml")
    if not isfile(sls_config):
        logger.error("Unable to locate serverless config file: {}".format(click.format_filename(sls_config)))

    sls = Serverless(sls_config)

    if not sls.has_function(function):
        logger.error("Missing function definition: {}".format(function))
        sys.exit(1)

    


