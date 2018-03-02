from __future__ import absolute_import

import logging

import click
import click_log

from stylist.click import StylistCli
from stylist.core import Stylist

CONTEXT_SETTINGS = dict(
    auto_envvar_prefix='STYLIST',
    obj=Stylist()
)

logger = logging.getLogger(__name__)
click_log.basic_config(logger)


cli = StylistCli(context_settings=CONTEXT_SETTINGS)

