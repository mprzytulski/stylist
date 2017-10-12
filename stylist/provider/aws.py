import boto3

from stylist.provider import Provider
from threads_aws_utils import SSM as BaseSSM


class AWSProvider(Provider):
    name = "aws"

    known_params = {
        "profile": ("AWS cli profile name for env {env_name}", {"type": str, "default": "default"})
    }

    @property
    def session(self):
        return boto3.Session(profile_name=self.profile)

    @property
    def ssm(self):
        class SSM(BaseSSM):
            def __init__(self, ssm, ctx):
                self.ssm = ssm
                self.ctx = ctx

            def get_full_parameters(self, *args, **kwargs):
                _all = []
                for resource in list(args):
                    _all += self._fetch_all_parameters(resource, kwargs.get('env', False))

                return _all

            def get_short_parameters(self, *args, **kwargs):
                kwargs['env'] = False
                params = self.get_parameters(*args, **kwargs)

                return {k.split('/')[-1]: v for k, v in params.items()}

            def _fetch_all_parameters(self, resource, env=False):
                namespace = self._resolve_namespace(resource)
                parameters = self.ssm.describe_parameters(
                    ParameterFilters=[
                        {
                            'Key': 'Name',
                            'Option': 'BeginsWith',
                            'Values': [
                                namespace,
                            ]
                        },
                    ],
                    MaxResults=50
                )

                values = self.get_parameters(resource, env=False, full=True)

                params = []
                for param in parameters.get('Parameters', []):
                    params.append([
                        self._normalize_name(param.get('Name'), env),
                        values.get(param.get('Name'), {}).get('Type'),
                        values.get(param.get('Name'), {}).get('Value'),
                        param.get('LastModifiedDate'),
                        param.get('LastModifiedUser'),
                    ])

                return params

            def write(self, namespace, parameter, value, encrypt):
                kms = self.ctx.provider.session.client("kms")

                key_id = None
                if encrypt:
                    aliases = kms.list_aliases()

                    key_id = (next(iter(filter(
                        lambda x: x.get('AliasName') == 'alias/parameter_store_key',
                        aliases.get('Aliases', {})
                    ))) or {}).get('TargetKeyId')

                if not key_id and encrypt:
                    raise Exception('Unable to locate KMS key with parameter_store_key alias and encryption required')

                full_name = self.get_full_name(*namespace.split(':'), parameter=parameter)

                args = {
                    'Name': full_name,
                    'Value': value,
                    'Type': 'SecureString' if encrypt else 'String',
                    'Overwrite': True
                }

                if encrypt:
                    args['KeyId'] = key_id

                self.ssm.put_parameter(**args)

                return full_name

            def delete(self, namespace, parameter):
                self.ssm.delete_parameter(
                    Name=self.get_full_name(*namespace.split(':'), parameter=parameter)
                )

        return SSM(self.session.client('ssm'), self.ctx)
