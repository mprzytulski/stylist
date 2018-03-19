class SSMException(Exception):
    pass


class SSM(object):
    def __init__(self, session):
        self.session = session
        self.ssm = session.client('ssm')

    def write(self, name, value, encrypt=True, tags=None):
        if not name:
            raise SSMException("You must provide parameter name")

        args = {
            'Name': name,
            'Value': value,
            'Type': 'SecureString' if encrypt else 'String',
            'Overwrite': True
        }

        if encrypt:
            args['KeyId'] = self._get_kms_key_by_name()

        self.ssm.put_parameter(**args)

        if not tags:
            return name

        self.ssm.add_tags_to_resource(
            ResourceType='Parameter',
            ResourceId=name,
            Tags=[{'Key': k, 'Value': v} for k, v in tags.items()]
        )

        return name

    def delete(self, name):
        return self.ssm.delete_parameter(
            Name=name
        )

    def get_full_parameters(self, *args):
        _all = []
        for resource in list(args):
            _all += self._fetch_all_parameters(resource)

        return _all

    def get_short_parameters(self, *args, **kwargs):
        kwargs['env'] = False
        kwargs['exclude_namespace'] = True
        params = self.get_parameters(*args, **kwargs)

        return params

    def get_parameters(self, namespace, full_object=False):
        next_token = -1
        parameters = {}

        while next_token != 0:
            search_params = {'Path': namespace, 'WithDecryption': True, 'Recursive': True}

            if next_token != -1:
                search_params['NextToken'] = next_token

            current_set = self.ssm.get_parameters_by_path(**search_params)

            for param in current_set.get('Parameters'):
                parameters[param.get('Name')] = param if full_object else param.get('Value')

            next_token = current_set.get('NextToken', 0)

        return parameters

    def find_by_tag(self, tag, value):
        params = self.ssm.describe_parameters(
            ParameterFilters=[{'Key': 'tag:{}'.format(tag), 'Option': 'Equals', 'Values': [value]}]
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

    def _get_kms_key_by_name(self, name='alias/parameter_store_key'):
        kms = self.session.client("kms")

        aliases = kms.list_aliases()

        key_id = (next(iter(filter(
            lambda x: x.get('AliasName') == name,
            aliases.get('Aliases', {})
        ))) or {}).get('TargetKeyId')

        if key_id:
            return key_id

        raise SSMException('Unable to locate KMS key with parameter_store_key alias and encryption required')

    def _fetch_all_parameters(self, resource):
        parameters = self.ssm.describe_parameters(
            ParameterFilters=[{'Key': 'Name', 'Option': 'BeginsWith', 'Values': [resource]}],
            MaxResults=50
        )

        values = self.get_parameters(resource, True)

        params = []
        for param in parameters.get('Parameters', []):
            params.append([
                param.get('Name'),
                values.get(param.get('Name'), {}).get('Type'),
                values.get(param.get('Name'), {}).get('Value'),
                param.get('LastModifiedDate'),
                param.get('LastModifiedUser'),
            ])

        return params

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
