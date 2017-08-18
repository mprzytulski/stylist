import sys
from os.path import join, isfile

import click
from terminaltables import AsciiTable, SingleTable

from stylist import Env
from stylist.cli import Context, GroupWithCommandOptions, pass_context, logger
from stylist.commands import global_options, ensure_project_directory, NotProjectDirectoryException
from stylist.lib.click.types import EventAwareFile
from stylist.lib.emulator import ExecutionContext
from stylist.lib.serverless import Serverless, FunctionNotFoundException
from stylist.lib.utils import highlight_json, tabulate_dict, display_section, table
from stylist.lib.virtualenv import Virtualenv


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
@click.option("--mode", "-m", type=click.Choice(['sns', 'api-gw', 'direct', 'server', "auto", "aws"]), default="auto",
              help="Execution mode")
@click.option("--cleanup", default=False, flag_value='cleanup', help="Remove virtualenv after execution")
@click.option("--force", default=False, flag_value='force', help="Force dependency installation")
@click.option("--event", default=False, flag_value='event', help="Display event details (may increase outout size)")
@click.argument("function_name")
@click.argument("source", type=EventAwareFile(mode="r"))
@pass_context
def invoke(ctx, function_name, source, mode, force, event, cleanup=False):
    sls_config = join(ctx.working_dir, "serverless.yml")
    if not isfile(sls_config):
        logger.error("Unable to locate serverless config file: {}".format(click.format_filename(sls_config)))

    sls = Serverless(sls_config, ctx)

    try:
        sls.ensure_function(function_name)
        lambda_function = sls.get_function(function_name)

        with Virtualenv(lambda_function.global_id, lambda_function.get_runtime(), cleanup) as venv:
            if venv.created or force:
                venv.pip.install_dependencies(
                    lambda_function.get_dependencies(True)
                )
                venv.pip.install_dependencies(["memory-profiler==0.47"])

            context = ExecutionContext(venv, ctx.environment, lambda_function)

            click.secho(
                click.style('Execution details for ', fg='green') +
                click.style(lambda_function.name, fg='red')
            )

            click.secho(
                table("EXECUTION CONTEXT", context.details).table
            )

            click.secho(
                table("ENVIRONMENT VARIABLES", context.environment_variables).table

            )

            event_data = source.read()

            if event or True:
                display_section("EVENT", highlight_json(event_data))

            click.echo("=" * click.get_terminal_size()[0] + "\n")

            result = context.execute(event_data)

            display_section("FUNCTION EXECUTION OUTPUT", highlight_json(result.stdout))

            click.secho(
                table("COLLECTED EVENTS", result.events, ["module", "function", "args"], wraped_col=2).table
            )

            click.secho(
                table("METRICS", result.stats).table
            )

            if result.stderr:
                display_section(
                    "FUNCTION ERROR OUTPUT", result.stderr, "red", "red"
                )
    except FunctionNotFoundException as e:
        logger.error(e.message)
        sys.exit(1)
