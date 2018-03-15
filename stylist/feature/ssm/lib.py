
class SSM(object):
    def __init__(self, session):
        self.session = session

    # def __init__(self, ssm, ctx):
    #     super(SSM, self).__init__(ssm)
    #     self.ctx = ctx

    def get_full_parameters(self, *args, **kwargs):
        _all = []
        for resource in list(args):
            _all += self._fetch_all_parameters(resource, kwargs.get('env', False))

        return _all

    def get_short_parameters(self, *args, **kwargs):
        kwargs['env'] = False
        kwargs['exclude_namespace'] = True
        params = self.get_parameters(*args, **kwargs)

        return params

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
                SSM.normalize_name(namespace, param.get('Name'), env, False),
                values.get(param.get('Name'), {}).get('Type'),
                values.get(param.get('Name'), {}).get('Value'),
                param.get('LastModifiedDate'),
                param.get('LastModifiedUser'),
            ])

        return params

    def write(self, namespace, parameter, value, encrypt=True, session=None, tags=None):
        kms = (session or self.ctx.provider.session).client("kms")

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

        if tags:
            self.ssm.add_tags_to_resource(
                ResourceType='Parameter',
                ResourceId=full_name,
                Tags=[{'Key': k, 'Value': v} for k, v in tags.items()]
            )

        return full_name

    def get_encryption_key(self):
        aliases = self.ctx.provider.session.client("kms").list_aliases()

        return next(iter(filter(
            lambda x: x.get('AliasName') == 'alias/parameter_store_key',
            aliases.get('Aliases', {})
        ))) or {}

    def find_by_tag(self, tag, value):
        params = self.ssm.describe_parameters(
            ParameterFilters=[{
                'Key': 'tag:{}'.format(tag),
                'Option': 'Equals',
                'Values': [value]
            }]
        )

        return map(
            lambda x: x.get('Name'),
            params.get('Parameters')
        )

    def find_by_tags(self, tags={}):
        params = self.ssm.describe_parameters(
            ParameterFilters=[
                {'Key': 'tag:{}'.format(tag), 'Option': 'Equals', 'Values': [value]} for tag, value in tags.items()
            ]
        )

        return map(
            lambda x: x.get('Name'),
            params.get('Parameters')
        )

    def delete(self, namespace, parameter):
        self.ssm.delete_parameter(
            Name=self.get_full_name(*namespace.split(':'), parameter=parameter)
        )

    @staticmethod
    def sync_vars(source, destination, namespace):
        """
        Sync SSM variables between profiles
        :type source SSM
        :type destination SSM
        :type namespace str
        :return:
        """
        return compare_dicts(
            source.get_short_parameters(namespace),
            destination.get_short_parameters(namespace)
        )
