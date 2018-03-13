from os.path import join, isdir

from stylist.feature import Feature
# from stylist.wrapper.chalice import Chalice, ChaliceException


class ChaliceFeature(Feature):
    """
    Use Chalice framework for fast microservice development with AWS Api Gateway and AWS Lambda
    """

    @property
    def installed(self):
        return isdir(join(self.stylist.working_dir, self.stylist.name))

    def _do_setup(self, init_args):
        try:
            apex = Chalice(self.stylist)
            apex.init(init_args)
        except ChaliceException as e:
            logger.error(e.message)
            logger.error(e.cmd)


