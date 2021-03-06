from __future__ import absolute_import

import base64
import glob
import json
import os
import subprocess
from os.path import dirname, join

import click


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

    def build(self, dockerfile_path, tag, custom_args):
        repository_name = self.get_repository_name(dockerfile_path)
        try:
            self.do_login('docker-images/python3')
        except:
            pass

        latest_tag = '{}:{}'.format(repository_name, 'latest')
        args = ['build', '-f', dockerfile_path, '-t', latest_tag] + list(custom_args) + [dirname(dockerfile_path)]

        self.run_docker(args)

        self.run_docker(['tag', latest_tag, '{}:{}'.format(repository_name, tag)])

        return '{}:{}'.format(repository_name, tag)

    def push(self, dockerfile_path, tag):
        repository_name = self.get_repository_name(dockerfile_path)

        try:
            repo = self.repositories.get_repository(repository_name)
        except Exception as e:
            self.repositories.create_repository(repository_name)
            repo = self.repositories.get_repository(repository_name)
            self.repositories.set_repository_policy(repository_name)
            self.repositories.set_lifecycle_policy(repository_name)

        self.do_login(repo)

        names = [self._do_push(repository_name, repo['repositoryUri'], tag)]

        if tag == 'latest':
            names.append(
                self._do_push(
                    repository_name,
                    repo['repositoryUri'],
                    self.get_latest_build_tag(dockerfile_path)
                )
            )

        return names

    def _do_push(self, repository_name, repository_uri, tag):
        local_name = '{name}:{tag}'.format(name=repository_name, tag=tag)
        remote_name = '{url}:{tag}'.format(url=repository_uri, tag=tag)

        args = ['tag', local_name, remote_name]
        click.secho("Tagged {local} -> {remote}".format(local=local_name, remote=remote_name), fg="blue")
        self.run_docker(args)

        args = ['push', remote_name]
        self.run_docker(args)

        return remote_name

    def images(self, docker_file):
        args = ['images', '--format', '{{json .}}', self.get_repository_name(docker_file)]
        process, out, err = self.run_docker(args, stdout=subprocess.PIPE)

        return [json.loads(line) for line in out.strip().split("\n") if line]

    def get_latest_build_tag(self, dockerfile_path):
        images = self.images(dockerfile_path)
        latest_hash = next(enumerate(filter(lambda x: x.get('Tag') == 'latest', images)))[1].get('ID')
        return next(
            enumerate(
                filter(lambda x: x.get('Tag') != 'latest' and x.get('ID') == latest_hash, images)
            )
        )[1].get('Tag')

    def do_login(self, repo):
        username, password, endpoint = self._get_authentication_data(repo)

        args = ['login', '-u', username, '-p', password, endpoint]
        self.run_docker(args)

    def _get_project_name(self):
        return '{project}'.format(project=self.ctx.name)

    def run_docker(self, flags, dockerfile_dir=None, stdout=None, stderr=None):
        args = ['docker'] + flags

        p = subprocess.Popen(
            args,
            stdout=stdout or click.get_text_stream('stdout'),
            stderr=stderr or click.get_text_stream('stderr'),
            cwd=dockerfile_dir
        )
        out, err = p.communicate()

        if p.returncode != 0:
            raise DockerException(args, err, p.returncode)

        return p, out, err

    def _get_authentication_data(self, repository):
        auth_data = self.ecr.get_authorization_token(
            registryIds=[repository.get('registryId')]
        ).get('authorizationData', [{}]).pop()

        return base64.b64decode(auth_data.get('authorizationToken')).decode().split(':') + [auth_data['proxyEndpoint']]

    def get_repository_name(self, dockerfile_path):
        dockerfile_base_path, dockerfile = os.path.split(dockerfile_path)

        parts = [
            '{}{}'.format(self.ctx.name.replace('.', '-'), dockerfile.replace('Dockerfile', '').replace('.', '/'))
        ]

        if self.subproject:
            parts += [self.subproject]

        return '/'.join(parts)


def _ask_about_docker_files(message, docker_files):
    click.secho(message, fg='blue')
    for i, docker_file in enumerate(docker_files):
        click.secho('  [{}] {}'.format(i + 1, docker_file), fg='blue')
    all_above = len(docker_files) + 1
    click.secho('  [{}] All above.'.format(all_above), fg='blue')

    docker_index = click.prompt(click.style('Build', fg='blue'), default=all_above)
    if docker_index == all_above:
        docker_files_indexes = tuple(range(0, len(docker_files)))
    else:
        docker_files_indexes = (docker_index - 1,)

    return docker_files_indexes


def _get_docker_files(ctx, ask, subproject):
    path = join(ctx.working_dir, subproject) if subproject else ctx.working_dir
    docker_files = glob.glob('{}/Dockerfile*'.format(path))

    if ask:
        return _ask_about_docker_files('Which docker file would you like to build?', docker_files)
    else:
        return docker_files
