from os.path import isdir

from stylist.feature import Feature
from stylist.feature.terraform.terraform import Terraform
from stylist.helper import Templates


class TerraformFeature(Feature):
    """
    Orchestrate infrastructure with terraform
    """
    def __init__(self, stylist):
        super(TerraformFeature, self).__init__(stylist)
        templates = Templates(stylist)
        self.terraform = Terraform(stylist, templates)

    @property
    def installed(self):
        return isdir(self.terraform.terraform_dir)

    def _do_setup(self, init_args):
        self.terraform.setup()
