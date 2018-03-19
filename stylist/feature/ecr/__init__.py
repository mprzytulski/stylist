from dependency_injector import providers

from stylist.feature import Feature
from stylist.feature.ecr.lib import ECRDockerRepository


class EcrFeature(Feature):
    @property
    def installed(self):
        return True

    def _do_setup(self, init_args):
        pass

    def on_config(self, stylist):
        stylist.docker_repositories.ecr = providers.Singleton(
            ECRDockerRepository, stylist=stylist, aws=stylist.main.aws
        )
