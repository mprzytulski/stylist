from stylist.feature import Feature


class ServerlessFeature(Feature):
    TEMPLATES = {
        "provider.tf": ''
    }

    def setup(self, ctx, templates):
        pass
