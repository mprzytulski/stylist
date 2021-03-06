from __future__ import absolute_import

import logging

import click
import click_log
import os

from stylist.click import CONTEXT_SETTINGS, ComplexCLI, Context

logger = logging.getLogger(__name__)
click_log.basic_config(logger)

stylist_context = click.make_pass_decorator(Context, ensure=True)
os.environ['STYLIST'] = "1"


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
def cli():
    pass
