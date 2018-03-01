from stylist.feature import Feature, FeatureException
from stylist.provider.sentry import proj_init_integration


class SentryFeature(Feature):
    """
    Error handling and reporting with sentry / raven.
    """

    @property
    def installed(self):
        ssm = self.stylist.provider.ssm

        return 'sentry' in ssm.get_short_parameters('service:{}'.format(self.stylist.name))

    def _do_setup(self, init_args):
        try:
            proj_init_integration(self.stylist)
        except KeyError:
            raise FeatureException('Failed to initialise sentry feature, please check stylist configuration.')
