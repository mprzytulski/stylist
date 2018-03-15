import boto3


class AwsSession(boto3.Session):
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None, region_name=None,
                 botocore_session=None, profile_name=None):
        super(AwsSession, self).__init__(aws_access_key_id, aws_secret_access_key, aws_session_token, region_name,
                                         botocore_session, profile_name)

        self.account_id = self.client('sts').get_caller_identity()["Account"]


class AWSProvider(object):
    name = "aws"

    def __init__(self, prefix=''):
        self._sessions = {}
        self.prefix = prefix

    def get_session(self, profile):
        """
        Get AWS session for given profile name
        :param profile: Full name of the profile used in configuration
        :return:
        """
        if profile not in self._sessions:
            self._sessions[profile] = AwsSession(profile_name=self.prefix + profile)

        return self._sessions[profile]

    # known_params = {
    #     "profile": ("AWS cli profile name for env {env_name}", {"type": str, "default": "default"})
    # }
    #
    # @property
    # def session(self):
    #     return self.get_session(self.profile)
    #
    # def get_session(self, profile):
    #     return boto3.Session(profile_name=profile)
    #
    # def get_session_for_stage(self, stage):
    #     return self.get_session(
    #         '{}{}'.format(
    #             self.ctx.settings.get('stylist', {}).get('provider', {}).get('prefix'),
    #             stage
    #         )
    #     )
    #
    # @property
    # def ssm(self):
    #     return SSM(self.session.client('ssm'), self.ctx)
    #
    # @property
    # def credentials(self):
    #     config = ConfigParser()
    #     config.read([os.path.expanduser('~/.aws/credentials')])
    #
    #     values = {
    #         'AWS_ACCESS_KEY_ID': config.get(self.profile, 'aws_access_key_id'),
    #         'AWS_SECRET_ACCESS_KEY': config.get(self.profile, 'aws_secret_access_key')
    #     }
    #
    #     config = ConfigParser()
    #     config.read([os.path.expanduser('~/.aws/config')])
    #     values['AWS_DEFAULT_REGION'] = config.get('profile ' + self.profile, 'region')
    #
    #     return values
