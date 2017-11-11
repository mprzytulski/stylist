import glob
import os
from copy import copy

import click
import subprocess

from os.path import join

import shutil

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.wrapper.apex import Apex, ApexException
from stylist.wrapper.docker import Docker

cli = copy(cli_prototype)
cli.short_help = "Helper for apex lambda functions"


@cli.command(help="Install function dependencies")
@click.option('--native', is_flag=True, default=False, help="Build with native module support via docker")
@stylist_context
def build(ctx, native):
    if native:
        docker = Docker(ctx, None)
        args = [
            'run', '--rm',
            '-v', '{}:/src'.format(os.getcwd()),
            'ctx.settings['docker_images']['python3-lambda']',
            'pip', 'install', '-r', '/src/requirements.txt', '--upgrade', '-t', '/src'
        ]

        p, out, err = docker.run_docker(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        p = subprocess.Popen(
            ['pip', 'install', '-r', 'requirements.txt', '-t', '.'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = p.communicate()


@cli.command(help="Clean dependencies after build")
@stylist_context
def clean(ctx):
    for file in [f for f in glob.glob('*') if f not in ('function.json', 'main.py', 'requirements.txt')]:
        try:
            shutil.rmtree(join(os.getcwd(), file))
        except OSError:
            try:
                os.unlink(join(os.getcwd(), file))
            except OSError:
                pass


@cli.command(help="Deploy apex function")
@click.argument('apex_args', nargs=-1, type=click.UNPROCESSED)
@stylist_context
def deploy(ctx, apex_args):
    try:
        apex = Apex(ctx)
        apex.deploy(apex_args)
    except ApexException as e:
        logger.error(e.message)
        logger.error(e.cmd)


@cli.command(help="Init apex project")
@click.option('--vpc', help="VPC name in which lambda functions should be placed")
@click.option('--security-group', help="List of security groups")
@click.option('--subnet', help="List of security groups")
@click.argument('apex_args', nargs=-1, type=click.UNPROCESSED)
@stylist_context
def init(ctx, vpc, security_group, subnet, apex_args):
    try:
        apex = Apex(ctx)
        apex.init(apex_args)
    except ApexException as e:
        logger.error(e.message)
        logger.error(e.cmd)
