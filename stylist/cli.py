from __future__ import absolute_import

import logging

import click
import click_log

from stylist.click import CONTEXT_SETTINGS, ComplexCLI, Context

logger = logging.getLogger(__name__)
click_log.basic_config(logger)

stylist_context = click.make_pass_decorator(Context, ensure=True)


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
def cli():
    pass
