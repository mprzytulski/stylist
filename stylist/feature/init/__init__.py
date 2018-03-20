
from stylist.feature import Feature


class InitFeature(Feature):
    @property
    def installed(self):
        return not self.stylist.initialised

    def _do_setup(self, init_args):
        pass
