import dependency_injector.providers as providers
from dependency_injector.containers import DynamicContainer

from stylist.feature import Feature
from stylist.feature.aws.provider import AWSProvider


class AwsFeature(Feature):
    @property
    def installed(self):
        return self.stylist.initialised

    def on_init(self, stylist):
        stylist.main.aws = providers.Singleton(
            AWSProvider,
            prefix=stylist.settings.stylist.aws.prefix or ''
        )
        stylist.containers['aws'] = DynamicContainer()

    def _do_setup(self, init_args):
        pass
