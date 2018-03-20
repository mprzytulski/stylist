from __future__ import absolute_import

import glob
import json
import random
import subprocess
from collections import OrderedDict

import click
import dockerfile

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
        """
        :return: DockerRepositoryCredentials
        """
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
        """
        List available containers
        :return:
        """
        base_name = '{}/Dockerfile'.format(self.project_dir)

        return {
            ((self.stylist.name + '-' + name.replace(base_name, '').strip('.-')).strip('.-')): name
            for name in glob.glob(base_name + '*')
        }

    def build(self, name, dockerfile, args):
        """
        Build docker images
        :param name:
        :param dockerfile:
        :param args:
        :return:
        """
        tag = ':'.join([name, 'latest'])
        cmd = DockerCommand(cwd=self.project_dir)
        cmd(
            'build', '-f', dockerfile, '-t', tag, *list(args) + [self.project_dir]
        )

        return tag

    def tag(self, build, tag):
        """
        Create tag for given build
        :param build:
        :param tag:
        :return:
        """
        DockerCommand()('tag', build, tag)

    def images(self, name):
        """
        List available images for given container
        :param name: Container name
        :return: list
        """
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
        """
        Get tag name to which latest tag is currently pointing to
        :param name: Container name
        :type name: str
        :return: str
        """
        images = self.images(name)
        latest_hash = next((x for x in images if str(x.get('Tag')) == 'latest'), None)

        return next(
            (x for x in images if x.get('Tag') != 'latest' and x.get('Id') == latest_hash.get('Id')), {}
        ).get('Tag')

    def push(self, name, repository, tag='latest'):
        """
        Push docker image with given tag to given repository
        :param name: Docker container name
        :param repository: Repository definition
        :param tag: Tag which should be pushed
        :type name: str
        :type repository: stylist.feature.docker.lib.DockerRepository
        :type tag: str
        :return: list
        """
        self.login(repository)
        names = [self._do_push(name, repository, tag)]

        if tag == 'latest':
            self.latest_tag(name)
            names.append(self._do_push(name, repository, self.latest_tag(name)))

        return names

    def login(self, repository):
        """
        Login to given docker repository
        :type repository: stylist.feature.docker.lib.DockerRepository
        :return:
        """
        credentials = repository.credentials
        cmd = DockerCommand(cwd=self.project_dir)
        cmd('login', '-u', credentials.user, '-p', credentials.password, credentials.endpoint)

    def enter(self, name, dockerfile_path, interactive=True, cmd='/bin/bash', docker_args=None, generator=False):
        """
        Run selected docker container
        """
        parsed = dockerfile.parse_file(unicode(dockerfile_path))

        workdir = next(iter(filter(
            lambda x: x.cmd == 'workdir',
            reversed(parsed)
        )), None)

        workdir = str(workdir.value[0]) if workdir else '/app'

        ports = map(
            lambda x: str(x.value[0]),
            filter(lambda x: x.cmd == 'expose', parsed)
        )

        if generator:
            yield 'Mounted: "{}" under "{}"'.format(self.stylist.working_dir, workdir)

        args = ['run', '--rm', '-v', '{}:{}'.format(self.stylist.working_dir, workdir)] + list(docker_args)

        port_prefix = str(random.randint(1, 6))
        for port in ports:
            host_port = port_prefix + port
            if generator:
                yield 'Exposed container port: {} on host port {}'.format(port, host_port)
            args += ['-p', '{host_port}:{port}'.format(port=port, host_port=host_port)]

        if interactive:
            args.append('-it')

        # @todo: implement env var support with AWS credentials
        args += [str(name), str(cmd)]

        cmd = DockerCommand(cwd=self.project_dir)
        cmd(*args)

    def _do_push(self, name, repository, tag):
        """
        Do the real push
        :type name: str
        :type repository: stylist.feature.docker.lib.DockerRepository
        :type tag: str
        :return:
        """
        local_name = '{name}:{tag}'.format(name=name, tag=tag)
        remote_name = '{url}:{tag}'.format(url=repository.uri, tag=tag)
        self.tag(local_name, remote_name)

        cmd = DockerCommand(cwd=self.project_dir)
        cmd('push', remote_name)

        return remote_name
