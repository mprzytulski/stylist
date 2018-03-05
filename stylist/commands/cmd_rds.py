import os
import re
import subprocess
import sys

import click
from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name

from stylist.cli import logger
from stylist.click.types import Boolean
from stylist.commands import GroupPrototype
from stylist.helper.rds import DbContext, get_connection_credentials

cli = GroupPrototype.create("Manage database creation / users / schemas")


def get_service_role_name(ctx):
    return re.sub("\W", "_", ctx.name + '_service')


def get_owner_role_name(ctx):
    return str(re.sub("\W", "_", ctx.name))


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
            "Execute following queries on db: '{}' (instance: {}): \n".format(db or 'default', instance), fg=fg
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
@click.option('--role', help="Create named role, create service role when '.' is provided as a name")
@click.option('--schema')
@click.pass_obj
def init(ctx, instance, db, schema, role):
    if len(filter(None, [db, schema, role])) != 1:
        logger.error('You need to provide value for one option db|role|schema')
        sys.exit(3)

    with DbContext(ctx, instance, get_connection_credentials(ctx, instance)) as context:
        role_name = db
        password = None
        ssm_key = None
        kms_tags = {}
        if db:
            if context.db_exists(db):
                logger.error("Can't initialise database. Database '{}' already exists.".format(db))
                sys.exit(1)

            if not context.role_exists(role_name):
                _, password = context.create_role(role_name)

            context.create_database(db, role_name)
            ssm_key = 'master:{}/{}'.format(instance, db)
            kms_tags = {'db': get_db_tag(instance, db)}
        elif role:
            role_name = re.sub("\W", "_", ctx.name + '_service') if role == '.' else role
            if context.role_exists(role_name):
                logger.error("Can't create role. Role '{}' already exists.".format(role_name))
                sys.exit(2)
            _, password = context.create_role(role_name, False)
            ssm_key = 'service:{}/{}'.format(ctx.name, instance)
            kms_tags = {'role': get_role_tag(instance, role_name)}
        elif schema:
            pass

        if not prompt(instance, db, context.queries, password):
            click.secho("Aborted!", fg="yellow")
            sys.exit(2)

        namespaces = {
            ssm_key: ('user', 'password', 'db', 'instance', 'host', 'port', 'schema')
        }

        write_parameters(
            ctx.provider.ssm, instance, db, namespaces, context.commit(), kms_tags
        )


@cli.command(name="drop", help="Drop database")
@click.option("--instance", default='rds-postgresql')
@click.option('--db')
@click.option('--schema')
@click.option('--role')
@click.pass_obj
def drop(ctx, instance, db, schema, role):
    if len(filter(None, [db, schema, role])) != 1:
        logger.error('You must provide only one db|schema|role')
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
                    type=Boolean(),
                    confirmation_prompt=(db is not None)
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
@click.pass_obj
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
@click.pass_obj
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


@cli.command(help="Generate RDS database credentials")
@click.option("--instance", default='rds-postgresql')
@click.option('--db', help='Use db owner credentials rather than instance')
@click.argument('command', nargs=-1, type=click.UNPROCESSED)
@click.pass_obj
def credentials(ctx, instance, db, command):
    credentials = {}
    with DbContext(ctx, instance, get_connection_credentials(ctx, instance, db)) as context:
        engine = context.get_instance_type(instance)
        mapping = {}

        if engine == 'postgres':
            mapping = {
                'host': 'PGHOST',
                'port': 'PGPORT',
                'db': 'PGDATABASE',
                'user': 'PGUSER',
                'password': 'PGPASSWORD'
            }
        elif engine == 'mysql':
            mapping = {
                'host': 'MYSQL_HOST',
                'port': 'MYSQL_PORT',
                'db': 'MYSQL_DB',
                'user': 'MYSQL_USER',
                'password': 'MYSQL_PWD'
            }

        if mapping:
            credentials = {mapping.get(k): v for k, v in context.credentials.items()}

    if command:
        credentials.update(os.environ)

        p = subprocess.Popen(
            command,
            stdout=click.get_text_stream('stdout'),
            stderr=click.get_text_stream('stderr'),
            env=credentials
        )
        p.communicate()
        sys.exit(p.returncode)
    else:
        for name, value in credentials.items():
            if any(word in os.environ['SHELL'] for word in ('bash', 'zsh')):
                pattern = 'export {}="{}"'
            elif 'fish' in os.environ['SHELL']:
                pattern = 'set -x {} "{}"'
            else:
                logger.error('Unknown shell')
                sys.exit(1)

            click.echo(pattern.format(name, value))
