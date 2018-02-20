from stylist.feature import Feature


class TerraformFeature(Feature):
    def setup(self, ctx):
        self.terraform.setup()
