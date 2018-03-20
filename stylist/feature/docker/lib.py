from __future__ import absolute_import

import glob
import json
import subprocess
from collections import OrderedDict

import click

from stylist.lib import which


class NotADockerProjectException(Exception):
    pass


class DockerRepository(object):
    def __init__(self, id, name, arn, uri, credentials=None):
        self.arn = arn
        self.id = id
        self.uri = uri
        self.name = name
        self._credentials = credentials

    @property
    def credentials(self):
        if callable(self._credentials):
            return self._credentials(self.id)
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        self._credentials = value


class DockerRepositoryCredentials(object):
    def __init__(self, user, password, endpoint):
        self.endpoint = endpoint
        self.password = password
        self.user = user


class DockerException(Exception):
    def __init__(self, cmd, message, errno):
        super(DockerException, self).__init__()
        self.cmd = cmd
        self.message = message
        self.errno = errno


class DockerRepositoryException(Exception):
    pass


class DockerCommand(object):
    def __init__(self, cwd=None, stdout=None, stderr=None):
        self.args = [which('docker')]
        self.kwargs = {}
        self.cwd = cwd
        self.stdout = stdout or click.get_text_stream('stdout')
        self.stderr = stderr or click.get_text_stream('stderr')
        self.output = ''

    def __call__(self, *args, **kwargs):
        p = subprocess.Popen(
            self.args + list(args),
            cwd=self.cwd,
            stdout=self.stdout,
            stderr=self.stderr
        )
        self.output, self.error = p.communicate()

        if p.returncode != 0:
            raise DockerException(args, self.error, p.returncode)


class Docker(object):
    def __init__(self, stylist, project_dir=None):
        self.project_dir = project_dir
        self.stylist = stylist

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def list_containers(self):
        base_name = '{}/Dockerfile'.format(self.project_dir)

        return {
            ((self.stylist.name + '-' + name.replace(base_name, '')).strip('-')): name
            for name in glob.glob(base_name + '*')
        }

    def build(self, name, dockerfile, args):
        tag = ':'.join([name, 'latest'])
        cmd = DockerCommand(cwd=self.project_dir)
        cmd(
            'build', '-f', dockerfile, '-t', tag, *list(args) + [self.project_dir]
        )

        return tag

    def tag(self, build, tag):
        DockerCommand()('tag', build, tag)

    def images(self, name):
        cmd = DockerCommand(
            cwd=self.project_dir,
            stdout=subprocess.PIPE
        )
        cmd('images', '--format', '{{json .}}', name)

        images = []
        for image in [json.loads(line) for line in cmd.output.strip().split("\n") if line]:
            images.append(OrderedDict([
                ('Id', image.get('ID')),
                ('Repository', image.get('Repository')),
                ('Tag', image.get('Tag')),
                ('VirtualSize', image.get('VirtualSize')),
                ('CreatedAt', image.get('CreatedAt'))
            ]))

        return images

    def latest_tag(self, name):
        images = self.images(name)
        latest_hash = next((x for x in images if str(x.get('Tag')) == 'latest'), None)

        return next(
            (x for x in images if x.get('Tag') != 'latest' and x.get('Id') == latest_hash.get('Id')), {}
        ).get('Tag')

    def push(self, name, repository, tag='latest'):
        self.login(repository)
        names = [self._do_push(name, repository, tag)]

        if tag == 'latest':
            self.latest_tag(name)
            names.append(self._do_push(name, repository, self.latest_tag(name)))

        return names

    def login(self, repository):
        credentials = repository.credentials
        cmd = DockerCommand(cwd=self.project_dir)
        cmd('login', '-u', credentials.user, '-p', credentials.password, credentials.endpoint)

    def _do_push(self, name, repository, tag):
        local_name = '{name}:{tag}'.format(name=name, tag=tag)
        remote_name = '{url}:{tag}'.format(url=repository.uri, tag=tag)
        self.tag(local_name, remote_name)

        cmd = DockerCommand(cwd=self.project_dir)
        cmd('push', remote_name)

        return remote_name
