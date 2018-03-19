class SSMException(Exception):
    pass


class SSM(object):
    def __init__(self, session, kms, key='parameter_store_key'):
        self.kms = kms
        self.key = key
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
            args['KeyId'] = self.kms.get_key_by_alias(self.key)

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
        return self.ssm.delete_parameter(Name=name)

    def get_parameters(self, namespace):
        parameters = {}
        search_params = {'Path': namespace, 'WithDecryption': True, 'Recursive': True}

        while search_params.get('NextToken', -1) != 0:
            current_set = self.ssm.get_parameters_by_path(**search_params)

            for param in current_set.get('Parameters'):
                parameters[param.get('Name')] = param.get('Value')

            search_params['NextToken'] = current_set.get('NextToken', 0)

        return parameters

    def describe_parameters(self, namespace):
        search_params = dict(
            ParameterFilters=[{'Key': 'Name', 'Option': 'BeginsWith', 'Values': [namespace]}],
            MaxResults=50
        )
        parameters = {}

        while search_params.get('NextToken', -1) != 0:
            current_set = self.ssm.describe_parameters(**search_params)

            for param in current_set.get('Parameters'):
                parameters[param.get('Name')] = param

            search_params['NextToken'] = current_set.get('NextToken', 0)

        values = self.get_parameters(namespace)

        params = {}
        for name, param in parameters.items():
            params[name] = [
                name,
                values.get(name, {}),
                param.get('Type'),
                param.get('LastModifiedDate'),
                param.get('LastModifiedUser'),
            ]

        return params

    # def find_by_tag(self, tag, value):
    #     params = self.ssm.describe_parameters(
    #         ParameterFilters=[{'Key': 'tag:{}'.format(tag), 'Option': 'Equals', 'Values': [value]}]
    #     )
    #
    #     return map(
    #         lambda x: x.get('Name'),
    #         params.get('Parameters')
    #     )
    #
    # def find_by_tags(self, tags={}):
    #     params = self.ssm.describe_parameters(
    #         ParameterFilters=[
    #             {'Key': 'tag:{}'.format(tag), 'Option': 'Equals', 'Values': [value]} for tag, value in tags.items()
    #         ]
    #     )
    #
    #     return map(
    #         lambda x: x.get('Name'),
    #         params.get('Parameters')
    #     )

    def _fetch_all_parameters(self, resource):
        parameters = self.ssm.describe_parameters(
            ParameterFilters=[{'Key': 'Name', 'Option': 'BeginsWith', 'Values': [resource]}],
            MaxResults=50
        )

        values = self.get_parameters(resource, True)

        params = {}
        for param in parameters.get('Parameters', []):
            params.update({
                'Name': param.get('Name'),
                'Type': values.get(param.get('Name'), {}).get('Type'),
                'Value': values.get(param.get('Name'), {}).get('Value'),
                'LastModifiedDate': param.get('LastModifiedDate'),
                'LastModifiedUser': param.get('LastModifiedUser'),
            })

        return params

    # @staticmethod
    # def sync_vars(source, destination, namespace):
    #     """
    #     Sync SSM variables between profiles
    #     :type source SSM
    #     :type destination SSM
    #     :type namespace str
    #     :return:
    #     """
    #     return compare_dicts(
    #         source.get_short_parameters(namespace),
    #         destination.get_short_parameters(namespace)
    #     )
