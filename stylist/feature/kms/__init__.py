from dependency_injector import providers

from stylist.feature import Feature
from stylist.feature.kms.lib import KMS


class KmsFeature(Feature):
    def __init__(self, stylist, key='parameter_store_key'):
        super(KmsFeature, self).__init__(stylist)
        self.key = key

    @property
    def installed(self):
        return self.stylist.initialised

    def _do_setup(self, init_args):
        pass

    def on_config(self, stylist):
        stylist.aws.kms = providers.Singleton(
            KMS, stylist=stylist, aws=stylist.main.aws
        )
