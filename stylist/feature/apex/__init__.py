import json
from collections import OrderedDict
from os.path import join, isfile

from stylist.feature import Feature, FeatureSetupException
# from stylist.wrapper.apex import Apex, ApexException


class ApexFeature(Feature):
    """
    Build and deploy your AWS lambda functions with apex.
    """
    @property
    def installed(self):
        return self.stylist.initialised and isfile(join(self.stylist.working_dir, 'project.json'))

    def _do_setup(self, init_args):
        try:
            apex = Apex(self.stylist)
            apex.init(init_args)

            with open(join(self.stylist.working_dir, 'project.json'), 'r+') as f:
                config = OrderedDict(json.load(f))

                if 'hooks' not in config:
                    config['hooks'] = {'build': 'stylist apex build',
                                       'clean': 'stylist apex clean'}
                    f.seek(0)
                    json.dump(config, f, indent=4)

        except ApexException as e:
            raise FeatureSetupException("Failed to initialise apex", e)

