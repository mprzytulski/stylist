import dependency_injector.providers as providers

from stylist.core import ConfigStorage as AbstractConfigStorage
from stylist.feature import Feature
from stylist.feature.ssm.lib import SSM


class ConfigStorage(AbstractConfigStorage):
    def __init__(self, stylist, aws):
        """
        Create SSM based ConfigStorage

        :type stylist: stylist.core.Stylist
        :type aws: stylist.feature.aws.provider.AWSProvider
        """
        super(ConfigStorage, self).__init__()
        self.aws = aws
        self.stylist = stylist
        self.ssm = None

    def __enter__(self, stage=None):
        self.ssm = SSM(self.aws.get_session(stage or self.stylist.profile))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ssm = None

    @property
    def name(self):
        return 'ssm'

    def get_parameter(self, name):
        return None

    def get_parameters(self, *paths):
        parameters = []
        for path in paths:
            parameters += self.ssm.get_full_parameters(path)

        return parameters

    def write(self, name, value, encrypt=True, tags=None):
        return self.ssm.write(name, value, encrypt, tags)

    def delete(self, name):
        return self.ssm.delete(name)

class SsmFeature(Feature):
    @property
    def installed(self):
        return True

    def _do_setup(self, init_args):
        pass

    def on_config(self, stylist):
        stylist.containers.get('config').ssm = providers.Singleton(
            ConfigStorage, stylist=stylist, aws=stylist.containers.get('global').aws
        )
