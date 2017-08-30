from __future__ import absolute_import

import base64
import subprocess
from os.path import isfile, dirname

import click
from git import Repo

from stylist.cli import logger
from stylist.lib.utils import find_dotenv


class NotADockerProjectException(Exception):
    pass


class DockerException(Exception):
    def __init__(self, message, errno):
        super(DockerException, self).__init__()
        self.message = message
        self.errno = errno


class Docker(object):
    class Repositories(object):
        def __init__(self, ecr):
            self.ecr = ecr

        def get_repository(self, name):
            repos = self.ecr.describe_repositories(repositoryNames=[name])

            return repos.get('repositories', [None]).pop()

        def create_repository(self, name):
            return self.ecr.create_repository(repositoryName=name)

    @property
    def dockerfile_path(self):
        return find_dotenv('Dockerfile', usecwd=True) or find_dotenv('Dockerfile', path=self.ctx.working_dir)

    def __init__(self, ctx):
        self.ctx = ctx
        self.ecr = ctx.provider.session.client('ecr')
        self.repositories = Docker.Repositories(self.ecr)
        self.project_name = self._get_project_name()

    def build(self, repository, tag=None, version='latest'):
        self._ensure_is_docker()

        args = ['build']
        args += ['-t', '{}:{}'.format(repository, tag)] if tag else []
        args.append(dirname(self.dockerfile_path))

        self.__run_docker(args)

    def push(self, tag):
        repo = self.repositories.get_repository(self.project_name)

        username, password, endpoint = self.__get_authentication_data(repo)

        args = ['login', '-u', username, '-p', password, endpoint]
        self.__run_docker(args)

        local_name = '{name}:{tag}'.format(name=self.project_name, tag=tag)
        remote_name = '{url}:{tag}'.format(url=repo['repositoryUri'], tag=tag)

        args = ['tag', local_name, remote_name]
        click.secho("Tagged {local} -> {remote}".format(local=local_name, remote=remote_name), fg="blue")
        self.__run_docker(args)

        args = ['push', remote_name]
        self.__run_docker(args)

        return remote_name

    def images(self):
        args = ['images', self.project_name]
        self.__run_docker(args)

    def _ensure_is_docker(self):
        if not isfile(self.dockerfile_path):
            logger.error('Not a docker project')
            raise NotADockerProjectException()

    def _get_project_name(self):
        repo = Repo(self.ctx.working_dir)
        origin = repo.remote('origin')
        name = origin.urls.next().split('/')[-1].replace('.git', '')

        return '{stage}/{project}'.format(stage=self.ctx.environment, project=name)

    def __run_docker(self, flags):
        args = ['docker'] + flags

        p = subprocess.Popen(args, stdout=click.get_text_stream('stdout'), stderr=click.get_text_stream('stderr'))
        out, err = p.communicate()

        if p.returncode != 0:
            raise DockerException(err, p.returncode)

        return True

    def __get_authentication_data(self, repository):
        auth_data = self.ecr.get_authorization_token(
            registryIds=[repository.get('registryId')]
        ).get('authorizationData', [{}]).pop()

        return base64.b64decode(auth_data.get('authorizationToken')).decode().split(':') + [auth_data['proxyEndpoint']]
