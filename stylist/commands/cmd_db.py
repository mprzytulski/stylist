from copy import copy

import click

from stylist.cli import stylist_context
from stylist.commands import cli_prototype
from stylist.helper.rds import DBManager

cli = copy(cli_prototype)
cli.short_help = "Manage database creation / users / schemas"


@cli.command(help="Create new database with db owner")
@click.option("--instance", default='rds-postgresql')
@click.argument("db")
@stylist_context
def initdb(ctx, instance, db):
    manager = DBManager(ctx)
    manager.initdb(instance, db)


@cli.command(help="Create new database schema inside existing database")
@click.option("--instance", default='rds-postgresql')
@click.option("--schema-name", default=None)
@click.argument("db")
@stylist_context
def initschema(ctx, instance, db, schema_name):
    schema_name = schema_name or ctx.name

    manager = DBManager(ctx)
    manager.initschema(instance, db, schema_name)


@cli.command(help="Grant service access to db / schema.")
@click.option("--instance", default='rds-postgresql')
@click.option("--schema", help="Schema to which access should be granted")
@click.argument('db')
@stylist_context
def grant(ctx, instance, schema, db):
    manager = DBManager(ctx)

    if not schema:
        manager.grant_db_access(instance, db)
    else:
        manager.grant_schema_access(instance, db, schema)
