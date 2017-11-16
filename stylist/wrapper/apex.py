import subprocess
from os.path import expanduser

import click
import os


class ApexException(Exception):
    def __init__(self, cmd, message, errno):
        super(ApexException, self).__init__()
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


class Apex(object):
    def __init__(self, ctx):
        super(Apex, self).__init__()
        self.ctx = ctx

    def run(self, args, dockerfile_dir=None, stdout=None, stderr=None):
        args = ['apex', '--profile', self.ctx.provider.profile, '-e', self.ctx.environment] + args

        p = subprocess.Popen(
            args,
            stdout=stdout or click.get_text_stream('stdout'),
            stderr=stderr or click.get_text_stream('stderr'),
            cwd=dockerfile_dir,
            env=dict(os.environ, **{'AWS_SHARED_CREDENTIALS_FILE': expanduser('~/.aws/credentials')})
        )
        out, err = p.communicate()

        if p.returncode != 0:
            raise ApexException(args, err, p.returncode)

        return p, out, err

    def init(self, apex_args):
        self.run(['init', '--skip-skeleton', '--no-prompt', '--name', self.ctx.name] + list(apex_args))

    def deploy(self, apex_args):
        self.run(['deploy'] + list(apex_args))

    @property
    def lambda_role_name(self):
        return '{}_lambda_function'.format(self.ctx.name)
