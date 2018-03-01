import glob
import json
import os
import shutil
import subprocess
from copy import copy
from os.path import join, isfile

import click

from stylist.cli import logger
from stylist.commands import cli_prototype
from stylist.wrapper.apex import Apex, ApexException
from stylist.wrapper.docker import Docker, DockerException

cli = copy(cli_prototype)
cli.short_help = "Helper for apex lambda functions"


@cli.command(help="Install function dependencies")
@click.option('--native', is_flag=True, default=False, help="Build with native module support via docker")
@click.pass_obj
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
                ctx.settings.get('docker_images')['python3_lambda'],
                'pip', 'install', '-r', '/src/req_all.txt', '--upgrade', '-t', '/src'
            ]

            # @todo - login to staging repository
            try:
                docker.do_login(
                    docker.repositories.get_repository('docker-images/python3-lambda')
                )
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

            if p.returncode != 0:
                logger.error(err)
    finally:
        if isfile('req_all.txt'):
            os.unlink('req_all.txt')


@cli.command(help="Clean dependencies after build")
@click.pass_obj
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
@click.pass_obj
def deploy(ctx, apex_args):
    try:
        apex = Apex(ctx)
        apex.deploy(apex_args)
    except ApexException as e:
        logger.error(e.message)
        logger.error(e.cmd)
