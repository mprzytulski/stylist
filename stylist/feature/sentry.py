import click

from stylist.feature import Feature, FeatureException
from stylist.provider.sentry import proj_init_integration


class SentryFeature(Feature):
    @property
    def installed(self):
        ssm = self.ctx.provider.ssm

        return 'sentry' in ssm.get_short_parameters('service:{}'.format(self.ctx.name))

    def _do_setup(self):
        try:
            proj_init_integration(self.ctx)
        except KeyError:
            raise FeatureException('Failed to initialise sentry feature, please check stylist configuration.')
