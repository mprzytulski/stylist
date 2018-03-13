from stylist.feature import Feature
from stylist.feature.aws.provider import AWSProvider
import dependency_injector.providers as providers


class AwsFeature(Feature):
    @property
    def installed(self):
        return False

    def __init__(self, stylist):
        super(AwsFeature, self).__init__(stylist)
        stylist.container.aws = providers.Singleton(AWSProvider)

    # def configure(self, stylist):pip instal
    #     stylist.registry(AWSProvider())

    def _do_setup(self, init_args):
        pass
