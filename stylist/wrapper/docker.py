from __future__ import absolute_import

import base64
import os
import subprocess

import click
from os.path import dirname


class NotADockerProjectException(Exception):
    pass


class DockerException(Exception):
    def __init__(self, cmd, message, errno):
        super(DockerException, self).__init__()
        self.cmd = cmd
        self.message = message
        self.errno = errno


REPOSITORY_PERMISSION_POLICY = """{
    "Version": "2008-10-17",
    "Statement": [
        {
            "Sid": "Allow pulls from ecs hosts",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com",
                "AWS": [
                    "arn:aws:iam::%s:role/ecs_host_role",
                    "arn:aws:iam::%s:root"
                ]
            },
            "Action": [
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:BatchCheckLayerAvailability"
            ]
        }
    ]
}"""

LIFECYCLE_POLICY = """
{
  "rules": [
    {
      "rulePriority": 10,
      "description": "Remove untagged images after 30 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 30
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
"""


class Docker(object):
    class Repositories(object):
        def __init__(self, ecr, ctx, subproject):
            self.ecr = ecr
            self.ctx = ctx
            self.subproject = subproject

        def get_repository(self, name):
            repos = self.ecr.describe_repositories(repositoryNames=[name])

            return repos.get('repositories', [None]).pop()

        def create_repository(self, name):
            self.ecr.create_repository(repositoryName=name)

        def set_repository_policy(self, name):
            self.ecr.set_repository_policy(
                repositoryName=name,
                policyText=REPOSITORY_PERMISSION_POLICY % (self.ctx.provider.account_id, self.ctx.provider.account_id)
            )

        def set_lifecycle_policy(self, name):
            self.ecr.put_lifecycle_policy(
                repositoryName=name,
                lifecyclePolicyText=LIFECYCLE_POLICY
            )

    def __init__(self, ctx, subproject):
        self.ctx = ctx
        self.ecr = ctx.provider.session.client('ecr')
        self.repositories = Docker.Repositories(self.ecr, self.ctx, subproject)
        self.project_name = self._get_project_name()
        self.subproject = subproject

    def build(self, dockerfile_path, tag):
        repository_name = self._get_repository_name(dockerfile_path)

        latest_tag = '{}:{}'.format(repository_name, 'latest')
        args = ['build', '-f', dockerfile_path, '-t', latest_tag, dirname(dockerfile_path)]

        self.__run_docker(args)

        self.__run_docker(['tag', latest_tag, '{}:{}'.format(repository_name, tag)])

        return '{}:{}'.format(repository_name, tag)

    def push(self, dockerfile_path):
        repository_name = self._get_repository_name(dockerfile_path)

        try:
            repo = self.repositories.get_repository(repository_name)
        except Exception as e:
            self.repositories.create_repository(repository_name)
            repo = self.repositories.get_repository(repository_name)
            self.repositories.set_repository_policy(repository_name)
            self.repositories.set_lifecycle_policy(repository_name)

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

    def images(self, docker_file):
        args = ['images', self._get_repository_name(docker_file)]
        self.__run_docker(args)

    def _get_project_name(self):
        return '{project}'.format(project=self.ctx.name)

    def __run_docker(self, flags, dockerfile_dir=None):
        args = ['docker'] + flags

        p = subprocess.Popen(
            args,
            stdout=click.get_text_stream('stdout'),
            stderr=click.get_text_stream('stderr'),
            cwd=dockerfile_dir
        )
        out, err = p.communicate()

        if p.returncode != 0:
            raise DockerException(args, err, p.returncode)

        return True

    def __get_authentication_data(self, repository):
        auth_data = self.ecr.get_authorization_token(
            registryIds=[repository.get('registryId')]
        ).get('authorizationData', [{}]).pop()

        return base64.b64decode(auth_data.get('authorizationToken')).decode().split(':') + [auth_data['proxyEndpoint']]

    def _get_repository_name(self, dockerfile_path):
        dockerfile_base_path, dockerfile = os.path.split(dockerfile_path)

        parts = [
            '{}{}'.format(self.ctx.name.replace('.', '-'), dockerfile.replace('Dockerfile', '').replace('.', '/'))
        ]

        if self.subproject:
            parts += [self.subproject]

        return '/'.join(parts)
