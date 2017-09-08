import shutil
from glob import glob

from os.path import join, basename

import click
import hcl
from click import style
from jinja2 import Environment, PackageLoader

from stylist.lib.click.types import Boolean
from stylist.lib.project.feature import Feature


class TerraformFeature(Feature):
    TEMPLATES = {
        "provider.tf": ''
    }

    def __init__(self):
        self.templates = Environment(
            loader=PackageLoader(__name__, 'templates'),
        )

