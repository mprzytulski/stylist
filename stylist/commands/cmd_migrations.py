import base64
from copy import copy

import click

from stylist.cli import stylist_context
from stylist.commands import cli_prototype
from stylist.utils import line_prefix
from stylist.wrapper.yoyo import Yoyo

cli = copy(cli_prototype)
cli.short_help = "Manage database migrations"


@cli.command(help="Create new database migration")
@click.option("--instance", default='rds-postgres')
@click.argument("db")
@click.argument("description")
@stylist_context
def new(ctx, instance, db, description):
    yoyo = Yoyo(ctx)
    yoyo.new_migration(instance, db, description)


@cli.command(help="Run migrations against database")
@click.option("--instance")
@click.option("--db")
@click.option("--revision")
@stylist_context
def apply(ctx, instance, db, revision):
    yoyo = Yoyo(ctx)
    yoyo.apply(instance, db, revision)


@cli.command(help="Rollback migrations")
@click.option("--instance")
@click.option("--db")
@click.option("--revision")
@stylist_context
def rollback(ctx, instance, db, revision):
    yoyo = Yoyo(ctx)
    yoyo.rollback(instance, db, revision)
