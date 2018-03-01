from copy import copy

import click

from stylist.commands import cli_prototype
from stylist.wrapper.yoyo import Yoyo

cli = copy(cli_prototype)
cli.short_help = "Manage database migrations"


@cli.command(help="Create new database migration")
@click.option("--instance", default='rds-postgresql')
@click.argument("db")
@click.argument("description")
@click.pass_obj
def new(ctx, instance, db, description):
    yoyo = Yoyo(ctx)
    yoyo.new_migration(instance, db, description)


@cli.command(help="Run migrations against database")
@click.option("--instance", help="Limit migrations only to specific server")
@click.option("--db", help="Limit migrations to specific database on given server instance")
@click.option("--revision")
@click.argument('yoyo_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def apply(ctx, instance, db, revision, yoyo_args):
    yoyo = Yoyo(ctx)
    yoyo.apply(instance, db, revision, yoyo_args)


@cli.command(help="Rollback migrations")
@click.option("--instance")
@click.option("--db")
@click.option("--revision")
@click.pass_obj
def rollback(ctx, instance, db, revision):
    yoyo = Yoyo(ctx)
    yoyo.rollback(instance, db, revision)
