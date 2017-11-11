from os.path import join, isfile

import click
from click import style

from stylist.click.types import Boolean
from stylist.feature import Feature


class ApexFeature(Feature):
    def setup(self, ctx):
        _docker = style('Apex', fg='blue')

        prompts = {
            "base_image": {"text": "Docker base image", "default": "python:3-stretch"},
        }
