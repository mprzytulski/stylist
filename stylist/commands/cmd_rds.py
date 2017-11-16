import sys
from copy import copy

import click
from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name
from stylist.helper.rds import DbContext

from stylist.cli import stylist_context, logger
from stylist.click.types import Boolean
from stylist.commands import cli_prototype

cli = copy(cli_prototype)
cli.short_help = "Manage database creation / users / schemas"


def get_connection_credentials(ctx, instance, db=None):
    """
    Return connection parameters for named instance

    If db name is provided function will return connection parameters for owner of that database
    otherwise it will return parameters for master user of given instance
    :param instance:
    :param db:
    :rtype: dict
    """
    ssm = ctx.provider.ssm
    db_params = ('host', 'port', 'user', 'password', 'schema')
    if not db:
        params = ssm.get_short_parameters('master:{}'.format(instance))
        return {k: v for k, v in params.items() if k in db_params}
    else:
        params = ssm.get_short_parameters(
            'master:{instance}/{db}'.format(instance=instance, db=db).format(instance)
        )
        return dict(
            host=params.get('{}/host'.format(db)),
            db=db,
            user=params.get('{}/user'.format(db)),
            password=params.get('{}/password'.format(db)),
            port=str(params.get('{}/port'.format(db))),
        )


def get_service_role_name(ctx):
    return ctx.name + '_service'


def get_owner_role_name(ctx):
    return str(ctx.name)


def get_db_tag(instance, db):
    return instance + '/' + db


def get_role_tag(instance, role_name):
    return instance + '/' + role_name


def prompt(instance, db, sqls, mask='-dummy-', fg="green"):
    queries = highlight(
        "\n".join(sqls).replace(mask or '-dummy-', '*' * 8),
        get_lexer_by_name('sql'),
        get_formatter_by_name('console')
    )

    return click.prompt(
        click.style(
            "Execute following queries on db: '{}' (instance: {}): \n".format(db, instance), fg=fg
        ) + queries,
        type=Boolean()
    )


def write_parameters(ssm, instance, db, namespaces, params, tags=None):
    for namespace, parameters in namespaces.items():
        for name, value in {k: v for k, v in params.items() if k in parameters}.items():
            ssm.write(namespace, name, value, tags=tags or {})

        click.secho(
            'Values for: [{}] has been stored under: "{}" namespace'.format(", ".join(parameters), namespace),
            fg="green"
        )


@cli.command(name="init", help="Create new database with db owner")
@click.option("--instance", default='rds-postgresql')
@click.option('--db')
@click.option('--schema')
@stylist_context
def init(ctx, instance, db, schema):
    if not (db or schema):
        logger.error('You need to provide value for at least one option db or schema')
        sys.exit(3)

    if db and schema:
        logger.error('You should provide only one option db|schema')
        sys.exit(4)

    with DbContext(ctx, instance, get_connection_credentials(ctx, instance)) as context:
        role_name = db
        password = None
        if db:
            if context.db_exists(db):
                logger.error("Can't initialise database. Database '{}' already exists.".format(db))
                sys.exit(1)

            if not context.role_exists(role_name):
                _, password = context.create_role(role_name)

            context.create_database(db, role_name)
        elif schema:
            pass

        if not prompt(instance, db, context.queries, password):
            click.secho("Aborted!", fg="yellow")
            sys.exit(2)

        namespaces = {
            'master:{}/{}'.format(instance, db): ('user', 'password', 'db', 'instance', 'host', 'port', 'schema')
        }

        write_parameters(
            ctx.provider.ssm, instance, db, namespaces, context.commit(), {'db': get_db_tag(instance, db)}
        )


@cli.command(name="drop", help="Drop database")
@click.option("--instance", default='rds-postgresql')
@click.option('--db')
@click.option('--schema')
@click.option('--role')
@stylist_context
def drop(ctx, instance, db, schema, role):
    if not any((db, schema, role)):
        logger.error('You need to provide value for at least one option db, schema or role')
        sys.exit(3)

    if len(filter(lambda x: x, (db, schema, role))) != 1:
        logger.error('You should provide only one option db|schema|role')
        sys.exit(4)

    with DbContext(ctx, instance, get_connection_credentials(ctx, instance)) as context:
        role_name = db
        ssm = ctx.provider.ssm
        parameters = {}

        if db:
            if not context.db_exists(db):
                logger.error("Can't drop database. Database '{}' doesn't exists.".format(db))
                sys.exit(1)

            context.drop_database(db)
            context.drop_role(role_name)

            parameters = ssm.find_by_tag('db', get_db_tag(instance, db))

        elif role:
            if not role.endswith('_service'):
                logger.error("Can't drop db owner role")
                sys.exit(1)

            if not context.role_exists(role):
                logger.error("Can't drop role. Role '{}' doesn't exists.".format(role))
                sys.exit(1)

            context.drop_role(role)
            parameters = ssm.find_by_tag('role', get_role_tag(instance, role))
        elif schema:
            # @todo drop schema
            pass

        if not prompt(instance, db, context.queries, fg="red"):
            click.secho("Aborted!", fg="yellow")
            sys.exit(2)

        if len(parameters):
            if not click.prompt(
                    'Operation will remove parameters stored under:\n{}\nContinue?'.format("\n".join(sorted(parameters))),
                    type=Boolean()
            ):
                click.secho("Aborted!", fg="yellow")
                sys.exit(2)

        try:
            context.commit()
        except Exception as e:
            logger.error(e.message)

        for param in parameters:
            ssm.ssm.delete_parameter(Name=param)

        click.secho("Done.", fg="green")


@cli.command(help="Grant service access to db / schema.")
@click.option("--instance", default='rds-postgresql')
@click.option("--schema", help="Schema to which access should be granted")
@click.option('--db', required=True)
@stylist_context
def grant(ctx, instance, db, schema):
    with DbContext(ctx, instance, get_connection_credentials(ctx, instance, db)) as context:
        role_name = get_service_role_name(ctx)
        role_tag = get_role_tag(instance, role_name)

        password = None
        params = {}
        if not context.role_exists(role_name):
            with DbContext(ctx, instance, get_connection_credentials(ctx, instance)) as instance_context:
                _, password = instance_context.create_role(role_name, False)

                if not prompt(instance, db, instance_context.queries, password):
                    click.secho("Aborted!", fg="yellow")
                    sys.exit(2)

                params = instance_context.commit()

        if not schema:
            context.grant_database_access(db, role_name)
        else:
            context.grant_schema_access(db, schema, role_name)

        if not prompt(instance, db, context.queries, password):
            click.secho("Aborted!", fg="yellow")
            sys.exit(2)

        namespaces = {
            'service:{}/db/{}'.format(ctx.name, instance): ('user', 'password', 'instance', 'host', 'port')
        }

        params.update(context.commit())
        write_parameters(
            ctx.provider.ssm, instance, db, namespaces, params,
            {'role': role_tag}
        )


@cli.command(help="Revoke service access to db / schema.")
@click.option("--instance", default='rds-postgresql')
@click.option("--schema", help="Schema to which access should be granted")
@click.option('--db', required=True)
@stylist_context
def revoke(ctx, instance, db, schema):
    with DbContext(ctx, instance, get_connection_credentials(ctx, instance, db)) as context:
        role_name = get_service_role_name(ctx)

        if not schema:
            context.revoke_database_access(db, role_name)
        else:
            context.revoke_schema_access(db, schema, role_name)

        if not prompt(instance, db, context.queries):
            click.secho("Aborted!", fg="yellow")
            sys.exit(2)

        context.commit()
