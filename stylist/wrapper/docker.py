from __future__ import absolute_import

import os
import base64
import subprocess

import botocore
import click
from botocore.errorfactory import ClientExceptionsFactory
from git import Repo


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

    def __init__(self, ctx):
        self.ctx = ctx
        self.ecr = ctx.provider.session.client('ecr')
        self.repositories = Docker.Repositories(self.ecr)
        self.project_name = self._get_project_name()

    def build(self, dockerfile_path, tag):
        repository_name = self._get_repository_name(dockerfile_path)

        for tag_name in [tag, 'latest']:
            args = ['build', '-f', dockerfile_path, '-t', '{}:{}'.format(repository_name, tag_name),
                    self.ctx.working_dir]
            self.__run_docker(args)

        return '{}:{}'.format(repository_name, tag)

    def push(self, dockerfile_path):
        repository_name = self._get_repository_name(dockerfile_path)

        try:
            repo = self.repositories.get_repository(repository_name)
        except Exception as e:
            repo = self.repositories.create_repository(repository_name)

        username, password, endpoint = self.__get_authentication_data(repo)

        args = ['login', '-u', username, '-p', password, endpoint]
        self.__run_docker(args)

        local_name = '{name}:{tag}'.format(name=repository_name, tag='latest')
        remote_name = '{url}:{tag}'.format(url=repo['repositoryUri'], tag='latest')

        args = ['tag', local_name, remote_name]
        click.secho("Tagged {local} -> {remote}".format(local=local_name, remote=remote_name), fg="blue")
        self.__run_docker(args)

        args = ['push', remote_name]
        self.__run_docker(args)

        return remote_name

    def images(self):
        args = ['images', self.project_name]
        self.__run_docker(args)

    def _get_project_name(self):
        return '{stage}/{project}'.format(stage=self.ctx.environment, project=self.ctx.name)

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

    def _get_repository_name(self, dockerfile_path):
        dockerfile_base_path, dockerfile = os.path.split(dockerfile_path)

        return '{}/{}{}'.format(self.ctx.environment,
                                self.ctx.name.replace('.', '_'),
                                dockerfile.replace('Dockerfile', '').replace('.', '/'))
