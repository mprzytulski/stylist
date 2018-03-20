import base64

from stylist.core import DockerRepositoryProvider
from stylist.feature.docker.lib import DockerRepository, DockerRepositoryException, DockerRepositoryCredentials

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


class ECRDockerRepositoryProvider(DockerRepositoryProvider):
    def __init__(self, stylist, aws):
        super(ECRDockerRepositoryProvider, self).__init__()
        self.session = aws.get_session(stylist.profile)
        self.stylist = stylist
        self.ecr = self.session.client('ecr')

    def create_repository(self, name, ignore_if_exists=False, with_permissions=True):
        try:
            self.ecr.create_repository(repositoryName=name)
        except self.ecr.exceptions.RepositoryAlreadyExistsException as e:
            if not ignore_if_exists:
                raise e

        if with_permissions:
            self._set_repository_policy(name)
            self._set_lifecycle_policy(name)

    def get_repository(self, name):
        repos = self.ecr.describe_repositories(repositoryNames=[name])
        data = repos.get('repositories', [None]).pop()

        if not data:
            raise DockerRepositoryException('Unable to locate repository: "{}"'.format(name))

        return DockerRepository(
            id=data.get('registryId'),
            name=data.get('repositoryName'),
            arn=data.get('repositoryArn'),
            uri=data.get('repositoryUri'),
            credentials=self._get_authentication_data
        )

    def _set_repository_policy(self, name):
        self.ecr.set_repository_policy(
            repositoryName=name,
            policyText=REPOSITORY_PERMISSION_POLICY % (self.session.account_id, self.session.account_id)
        )

    def _set_lifecycle_policy(self, name):
        self.ecr.put_lifecycle_policy(
            repositoryName=name,
            lifecyclePolicyText=LIFECYCLE_POLICY
        )

    def _get_authentication_data(self, registry_id):
        auth_data = self.ecr.get_authorization_token(
            registryIds=[registry_id]
        ).get('authorizationData', [{}]).pop()

        return DockerRepositoryCredentials(
            *base64.b64decode(auth_data.get('authorizationToken')).decode().split(':') + [auth_data['proxyEndpoint']]
        )
