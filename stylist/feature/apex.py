from click import style

from stylist.feature import Feature


class ApexFeature(Feature):
    """
    Build and deploy your AWS lambda functions with apex.
    """

    @property
    def installed(self):
        return False

    def _do_setup(self):
        _docker = style('Apex', fg='blue')

        prompts = {
            "base_image": {"text": "Docker base image", "default": "python:3-stretch"},
        }
