from __future__ import absolute_import

import logging

import click
import click_log

from stylist.click import ComplexCLI, CONTEXT_SETTINGS, Context

logger = logging.getLogger(__name__)

stylist_context = click.make_pass_decorator(Context, ensure=True)


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click_log.init(__name__)
def cli():
    pass
