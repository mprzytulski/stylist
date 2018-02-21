from stylist.feature import Feature
from stylist.provider.sentry import proj_init_integration


class SentryFeature(Feature):
    def setup(self, ctx):
        proj_init_integration(ctx)
