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
@click.option("--superuser", is_flag=True, default=False)
@click.argument("db")
@click.argument("description")
@stylist_context
def new(ctx, instance, db, superuser, description):
    yoyo = Yoyo(ctx)
    yoyo.new_migration(instance, db, superuser, description)


@cli.command(help="Run migrations against database")
@click.option("--instance")
@click.option("--db")
@click.option("--revision")
@stylist_context
def apply(ctx, instance, db, revision):
    yoyo = Yoyo(ctx)
    yoyo.apply(instance, db, revision)


@cli.command(help="Create new database with db owner")
@click.option("--instance", default='rds-postgres')
@click.argument("db")
@stylist_context
def initdb(ctx, instance, db):
    yoyo = Yoyo(ctx)
    yoyo.initdb(instance, db)


@cli.command(help="Create new database schema inside existing database")
@click.option("--instance", default='rds-postgres')
@click.option("--schema-name", default=None)
@click.argument("db")
@stylist_context
def initschema(ctx, instance, db, schema_name):
    schema_name = schema_name or ctx.name

    yoyo = Yoyo(ctx)
    yoyo.initschema(instance, db, schema_name)


@cli.command(help="Grant service access to db.")
@click.option("--instance", default='rds-postgres')
@click.option("--service")
@click.argument("db")
@stylist_context
def grant(ctx, instance, service, db):
    yoyo = Yoyo(ctx)
    yoyo.grant(instance, service, db)


@cli.command(help="Rollback migrations")
@click.option("--instance")
@click.option("--db")
@click.option("--revision")
@stylist_context
def rollback(ctx, instance, db, revision):
    yoyo = Yoyo(ctx)
    yoyo.rollback(instance, db, revision)
