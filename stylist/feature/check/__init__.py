
from stylist.feature import Feature


class CheckFeature(Feature):
    @property
    def installed(self):
        return True

    def _do_setup(self, init_args):
        pass
