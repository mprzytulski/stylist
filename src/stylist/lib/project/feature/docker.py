from glob import glob

from os.path import join

from stylist.lib.project.feature import Feature


class DockerFeature(Feature):
    TEMPLATES = {
        "provider.tf": ''
    }

    def setup(self, ctx, templates):
        pass
