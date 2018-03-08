from stylist.feature import Feature


class DeployFeature(Feature):
    @property
    def installed(self):
        return False

    def _do_setup(self, init_args):
        pass
