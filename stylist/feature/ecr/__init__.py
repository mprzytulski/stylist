from dependency_injector import providers

from stylist.feature import Feature
from stylist.feature.ecr.lib import ECRDockerRepositoryProvider


class EcrFeature(Feature):
    @property
    def installed(self):
        return self.stylist.initialised

    def _do_setup(self, init_args):
        pass

    def on_config(self, stylist):
        stylist.docker_repositories.ecr = providers.Singleton(
            ECRDockerRepositoryProvider, stylist=stylist, aws=stylist.main.aws
        )
