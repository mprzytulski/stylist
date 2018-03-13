from stylist.core import ConfigStorage as AbstractConfigStorage
from stylist.feature.aws import AwsFeature


class ConfigStorage(AbstractConfigStorage):
    @property
    def name(self):
        return 'ssm'


class SsmFeature(AwsFeature):

