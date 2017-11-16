import subprocess
from os.path import join

import click
import os


class ChaliceException(Exception):
    def __init__(self, cmd, message, errno):
        super(ChaliceException, self).__init__()
        self.cmd = cmd
        self.message = message
        self.errno = errno


class ApexContext(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Chalice(object):
    def __init__(self, ctx):
        super(Chalice, self).__init__()
        self.ctx = ctx

    def run(self, args, stdout=None, stderr=None, cwd=None):
        args = ['chalice'] + args + ['--profile', self.ctx.provider.profile]

        p = subprocess.Popen(
            args,
            stdout=stdout or click.get_text_stream('stdout'),
            stderr=stderr or click.get_text_stream('stderr'),
            cwd=cwd or join(self.ctx.working_dir, self.ctx.name),
            env=os.environ
        )
        out, err = p.communicate()

        if p.returncode != 0:
            raise ChaliceException(args, err, p.returncode)

        return p, out, err

    def init(self, chalice_args):
        self.run(['new-project', self.ctx.name] + list(chalice_args), cwd=self.ctx.working_dir)

    def deploy(self, chalice_args):
        self.run([
                'deploy',
                '--stage', self.ctx.environment,
                '--api-gateway-stage', self.ctx.environment
            ] + list(chalice_args)
        )

    @property
    def lambda_role_name(self):
        return '{}_lambda_function'.format(self.ctx.name)
