import glob
import json
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
    with open('.project_files', 'w+') as f:
        json.dump(glob.glob("*"), f)

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
    with open('.project_files') as f:
        project_files = json.load(f)

    try:
        for dependency_file in [f for f in glob.glob('*') if f not in project_files]:
            try:
                shutil.rmtree(join(os.getcwd(), dependency_file))
            except OSError:
                try:
                    os.unlink(join(os.getcwd(), dependency_file))
                except OSError:
                    pass
    finally:
        os.unlink('.project_files')


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

        with open(join(ctx.working_dir, 'project.json'), 'r+') as f:
            config = json.load(f)

            if 'hooks' not in config:
                config['hooks'] = {
                    'build': 'apex build',
                    'clean': 'apex clean'
                }
                json.dump(config, f)

    except ApexException as e:
        logger.error(e.message)
        logger.error(e.cmd)
