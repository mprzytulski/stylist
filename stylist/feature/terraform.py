import os

from os.path import isdir

from stylist.feature import Feature


class TerraformFeature(Feature):
    @property
    def installed(self):
        return isdir(self.terraform.terraform_dir)

    def _do_setup(self):
        self.terraform.setup()
