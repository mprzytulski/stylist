import dependency_injector.providers as providers

from stylist.feature import Feature
from stylist.feature.aws.provider import AWSProvider


class AwsFeature(Feature):
    @property
    def installed(self):
        return True

    def on_init(self, stylist):
        stylist.containers.get('global').aws = providers.Singleton(AWSProvider)

    def _do_setup(self, init_args):
        pass
