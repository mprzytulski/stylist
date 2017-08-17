import json
import os
import shutil
import subprocess
import sys
import tempfile
from os.path import join, isfile, isdir, dirname, realpath

import click
from pygments import highlight, lexers, formatters
from tabulate import tabulate

from stylist import Env
from stylist.cli import Context, GroupWithCommandOptions, pass_context, logger
from stylist.commands import global_options, ensure_project_directory, NotProjectDirectoryException
from stylist.lib.serverless import Serverless, FunctionNotFoundException
from stylist.lib.utils import colourize
from stylist.lib.wrapper.pip import install_dependencies
from stylist.lib.wrapper.virtualenv import create_env


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
@click.argument("source", type=click.File(mode="r"))
@pass_context
def invoke(ctx, function_name, source, mode, force, event, shutill=None, cleanup=False):
    sls_config = join(ctx.working_dir, "serverless.yml")
    if not isfile(sls_config):
        logger.error("Unable to locate serverless config file: {}".format(click.format_filename(sls_config)))

    sls = Serverless(sls_config)

    try:
        sls.ensure_function(function_name)

        env_dir = None
        try:
            lambda_function = sls.get_function(function_name)

            env_dir = join(tempfile.gettempdir(), "venv-{service}-{function}".format(
                service=sls.name,
                function=lambda_function.name
            ))

            require_dependency_installation = True
            venv_created = False
            if not isdir(env_dir):
                venv_created = True
                click.secho("Creating temporary virtualenv: {}".format(click.format_filename(env_dir)), fg="green")
                create_env(env_dir, lambda_function.get_runtime())
            else:
                require_dependency_installation = False
                click.secho("Using existing virtualenv", fg="blue")

            bin_dir = join(env_dir, "bin")

            dependencies = lambda_function.get_dependencies(True)
            if require_dependency_installation or force:
                click.secho("Installing dependencies", fg="green")
                install_dependencies(
                    bin_dir,
                    dependencies,
                    click
                )

                install_dependencies(
                    bin_dir,
                    ["memory-profiler==0.47"],
                    click,
                    True
                )

            click.secho("Creating execution wrapper")

            handler_module, handler_function = lambda_function.handler.split(".")

            with open(join(env_dir, "wrapper.py"), "w+") as wrapper:
                wrapper.write(WRAPPER_TEMPLATE.format(
                    module=handler_module,
                    handler=handler_function,
                    function_dir=lambda_function.function_dir,
                    stylist_lib_dir=realpath(join(dirname(__file__), "../../"))
                ))

            env = lambda_function.get_environment()
            env["SENTRY_ENABLED"] = "false"

            click.echo(click.style('Execution details for ', fg='green') + click.style(lambda_function.name, fg='red'))
            click.echo()

            click.secho("EXECUTION CONTEXT: ", fg="blue")
            click.echo(tabulate(
                [
                    ("ENVIRONMENT", colourize(ctx.environment)),
                    ("VIRTUALENV", env_dir),
                    ("NEW VIRUTALENV", venv_created),
                    ("DEPENDENCIES", ", ".join(dependencies)),
                    ("RUNTIME", lambda_function.get_runtime()),
                ],
                headers=["Name", "Value"]
            ) + "\n")

            click.secho("ENVIRONMENT VARIABLES: ", fg="blue")
            click.echo(tabulate(
                [(key, val) for key, val in env.items()],
                headers=["Name", "Value"]
            ) + "\n")

            event_source = source.read()

            if event:
                formatted_json = json.dumps(json.load(event_source), sort_keys=True, indent=4)

                colorful_json = highlight(
                    unicode(formatted_json, 'UTF-8'),
                    lexers.JsonLexer(),
                    formatters.TerminalFormatter()
                )

                click.secho("EVENT: ", fg="blue")
                click.echo(colorful_json)

            click.echo("=" * click.get_terminal_size()[0] + "\n")

            p = subprocess.Popen(
                [join(bin_dir, "python"), "wrapper.py"],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=env_dir,
                env=env
            )

            p.stdin.write(event_source)

            stdout, stderr = p.communicate()

            click.secho("FUNCTION EXECUTION OUTPUT: ", fg="blue")

            output = json.loads(stdout)

            try:
                formatted_json = json.dumps(output["result"], sort_keys=True, indent=4)

                colorful_json = highlight(
                    unicode(formatted_json, 'UTF-8'),
                    lexers.JsonLexer(),
                    formatters.TerminalFormatter()
                )

                click.secho(colorful_json)
            except Exception as e:
                print e.message
                click.secho(stdout, fg="yellow")

            if stderr:
                click.secho("FUNCTION ERROR OUTPUT: ", fg="red")
                click.secho(stderr, fg="red")

            click.secho("COLLECTED EVENTS: ", fg="blue")

            rows = []
            for module, functions in output["events"].items():
                for function, calls in functions.items():
                    for call in calls:
                        rows.append((module, function, json.dumps(call)))

            click.echo(
                tabulate(
                    rows,
                    headers=("module", "function", "args")
                ) + "\n"
            )

            click.secho("METRICS: ", fg="blue")
            click.echo(
                tabulate(
                    [(k.upper(), v) for k, v in output["stats"].items()],
                    headers=["Name", "Value"]
                )
            )

        finally:
            if os.path.exists(env_dir) and cleanup:
                shutil.rmtree(env_dir)
    except FunctionNotFoundException as e:
        logger.error(e.message)
        sys.exit(1)


WRAPPER_TEMPLATE = """
# vim:fileencoding=utf-8
# This file is generated on the fly
import os
import sys
import json

root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path[0:0] = ["{function_dir}"]
sys.path.append("{stylist_lib_dir}")

from stylist.lib.wrapper import execute

raw_event = json.load(sys.stdin)

def get_handler():
    import {module}
    from {module} import {handler} as real_handler

    return real_handler, {module}

execute(get_handler, raw_event, {{}})
"""
