import glob
import json
import os
from copy import copy

import click
import subprocess

from os.path import join, isfile

import shutil

from stylist.cli import stylist_context, logger
from stylist.commands import cli_prototype
from stylist.wrapper.apex import Apex, ApexException
from stylist.wrapper.docker import Docker, DockerException

cli = copy(cli_prototype)
cli.short_help = "Helper for apex lambda functions"


@cli.command(help="Install function dependencies")
@click.option('--native', is_flag=True, default=False, help="Build with native module support via docker")
@stylist_context
def build(ctx, native):
    with open('.project_files', 'w+') as f:
        json.dump(glob.glob("*"), f)

    try:
        global_req = ""
        for req_file in [join(ctx.working_dir, 'requirements.txt'), join(os.getcwd(), 'requirements.txt')]:
            if not isfile(req_file):
                continue
            with open(req_file, 'r') as f:
                global_req += f.read() + "\n"

        with open(join(os.getcwd(), "req_all.txt"), "w+") as f:
            f.write(global_req)

        if native:
            docker = Docker(ctx, None)

            args = [
                'run', '--rm',
                '-v', '{}:/src'.format(os.getcwd()),
                '946211468949.dkr.ecr.eu-west-1.amazonaws.com/docker-images/python3-lambda',
                'pip', 'install', '-r', '/src/req_all.txt', '--upgrade', '-t', '/src'
            ]

            try:
                docker.do_login(docker.repositories.get_repository('docker-images/python3-lambda'))
            except DockerException as e:
                logger.error(e)
            p, out, err = docker.run_docker(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(
                ['pip', 'install', '-r', 'req_all.txt', '-t', '.'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out, err = p.communicate()
    finally:
        if isfile('req_all.txt'):
            os.unlink('req_all.txt')


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
