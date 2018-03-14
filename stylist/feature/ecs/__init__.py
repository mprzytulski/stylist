from stylist.feature import Feature
from stylist.feature.aws import AwsFeature


class EcsFeature(Feature):
    @property
    def installed(self):
        pass

    def _do_setup(self, init_args):
        pass
