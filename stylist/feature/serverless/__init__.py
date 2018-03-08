from stylist.feature import Feature


class ServerlessFeature(Feature):
    @property
    def installed(self):
        return False

    def _do_setup(self, init_args):
        pass
