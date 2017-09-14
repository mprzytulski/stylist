import subprocess
import sys
from copy import copy
from glob import glob
from os.path import join, basename, isfile

import boto3
import click
import yaml

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.click.types import EventAwareFile
from stylist.emulator import ExecutionContext
from stylist.emulator.aws import Emulator
from stylist.wrapper.serverless import Serverless, FunctionNotFoundException, InvalidContextException
from stylist.utils import highlight_json, display_section, table
from stylist.wrapper.virtualenv import Virtualenv

cli = copy(cli_prototype)
cli.short_help = 'Manage serverless functions'

sns = boto3.client('sns')


@cli.command(help='Invoke serverless lambda function with predefined event')
@click.option('--mode', '-m', type=click.Choice(['sns', 'api-gw', 'direct', 'auto']), default='auto',
              help='Execution mode')
@click.option('--cleanup', default=False, flag_value='cleanup', help='Remove virtualenv after execution')
@click.option('--force', default=False, flag_value='force', help='Force dependency installation')
@click.option('--event', default=False, flag_value='event', help='Display event details (may increase outout size)')
@click.argument('function_name')
@click.argument('source', type=EventAwareFile(mode='r'))
@stylist_context
def invoke(ctx, function_name, source, mode, force, event, cleanup=False):
    try:
        sls = Serverless.from_context(ctx)
        sls.ensure_function(function_name)
        lambda_function = sls.get_function(function_name)

        with Virtualenv(lambda_function.global_id, lambda_function.get_runtime(), cleanup) as venv:
            if venv.created or force:
                venv.pip.install_dependencies(lambda_function.get_dependencies(True))
                venv.pip.install_dependencies(['memory-profiler==0.47'])

            context = ExecutionContext(venv, ctx.environment, lambda_function)

            click.secho(
                click.style('Execution details for ', fg='green') +
                click.style(lambda_function.name, fg='red')
            )

            click.secho(table('EXECUTION CONTEXT', context.details).table)
            click.secho(table('ENVIRONMENT VARIABLES', context.environment_variables).table)

            emulator = Emulator(mode, source.read(), lambda_function)

            if event or True:
                display_section('EVENT', highlight_json(emulator.emulate()))

            click.echo('=' * click.get_terminal_size()[0] + '\n')

            result = context.execute(emulator.emulate())

            display_section('FUNCTION EXECUTION OUTPUT', highlight_json(result.stdout))

            click.secho(
                table('COLLECTED EVENTS', result.events, ['module', 'function', 'args'], wraped_col=2).table
            )

            click.secho(table('METRICS', result.stats).table)

            if result.stderr:
                display_section('FUNCTION ERROR OUTPUT', result.stderr, 'red', 'red')
    except InvalidContextException:
        logger.error('Invalid context - check your serverless.yml file')
        sys.exit(1)
    except FunctionNotFoundException as e:
        logger.error(e.message)
        sys.exit(2)


@cli.command(help='List all named events known for given function name')
@click.argument('function_name')
@stylist_context
def events(ctx, function_name):
    try:
        sls = Serverless.from_context(ctx)
        sls.ensure_function(function_name)

        lambda_function = sls.get_function(function_name)
        for f in glob(join(lambda_function.function_dir, '.events', '*.json')):
            click.echo('- ' + basename(f).replace('.json', ''))

    except InvalidContextException:
        logger.error('Invalid context - check your serverless.yml file')
        sys.exit(1)
    except FunctionNotFoundException as e:
        logger.error(e.message)
        sys.exit(2)


@cli.command(help='Deploy lambda function')
@stylist_context
def deploy(ctx):
    if not isfile('./serverless.yml'):
        raise Exception('No "serverless.yml" file in your current directory')

    with open('./serverless.yml') as f:
        serverless_yml = yaml.load(f.read())

    _create_missing_sns(serverless_yml)

    subprocess.call(['sls', 'deploy', '--stage', ctx.environment])


def _create_missing_sns(serverless_yml):
    def _extract_sns(name):
        return name.split('sns_topic_', 1)[1].replace('}', '')

    for function_name in serverless_yml['functions'].keys():
        for value in serverless_yml['functions'][function_name]['events']:
            if 'sns' in value:
                sns.create_topic(Name=_extract_sns(value['sns']))
