import re
import sys

import click
from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name

from stylist.cli import logger
from stylist.click.types import Boolean
from stylist.helper.rds.flavors import MySQLFlavor, PostgreSQLFlavor
from stylist.utils import random_password


class NotSupportedEngineException(Exception):
    pass


def get_dsn_parameters(ctx, ssm, superuser, instance, db):
    resource_params_id = '/resource/{instance}/{db}/'.format(instance=instance, db=db)
    resource_id = resource_params_id.replace('/resource/', 'resource:')

    """ If migrations are for different database than master we use service credentials, otherwise use master"""
    if not superuser:
        service_params_id = '/service/{name}/{instance}/{db}/'.format(instance=instance, db=db,
                                                                      name=ctx.name)
        service_id = service_params_id.replace('/service/', 'service:')
        migration_table = 'migrations_' + ctx.name
    else:
        service_params_id = '/master/{instance}/'.format(instance=instance)
        service_id = service_params_id.replace('/master/', 'master:')
        migration_table = 'migrations_superuser_' + ctx.name

    db_params = {}
    exec_params = {}

    for key, value in ssm.get_parameters(service_id, env=False).items():
        db_params[key.replace(service_params_id, '')] = value

    for key, value in ssm.get_parameters(resource_id, env=False).items():
        exec_params[ssm._normalize_name(key, True)] = value
        db_params[key.replace(resource_params_id, '')] = value

    migration_table = re.sub('\W', '_', migration_table)

    return service_id, migration_table, db_params, exec_params


class ExecutionContext(object):
    def __init__(self, ctx, instance):
        self.ctx = ctx
        self.instance = instance
        self.sqls = []
        self.password = random_password()

    def __enter__(self):
        self.flavor = self._get_flavor()

        self.params = self.ctx.provider.ssm.get_short_parameters('master:{}'.format(self.instance))
        self.params['db'] = self.flavor.get_connection_db()

        self.service_params = {}

        self.connection = self.flavor.get_connection(**self.params)
        self.cursor = self.connection.cursor()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.connection.close()

    def db_exists(self, db):
        self.cursor.execute(self.flavor.db_exists_sql(db))
        return self.cursor.fetchone()

    def db_create(self, name, owner):
        if not self.user_exists(owner):
            self.user_create(owner)

        self.sqls += self.flavor.create_db_sql(name, 'UTF-8', owner)
        self.service_params['db'] = name

    def grant_db_access(self, user, database):
        if not self.user_exists(user):
            self.user_create(user)

        self.sqls += self.flavor.grant_permission_sql(user, database)

    def user_exists(self, user):
        self.cursor.execute(self.flavor.user_exists_sql(user))

        return self.cursor.fetchone()

    def user_create(self, user):
        self.sqls += self.flavor.create_user_sql(user, self.password)
        self.service_params['user'] = user
        self.service_params['password'] = self.password

    def schema_exists(self, name):
        self.cursor.execute(self.flavor.schema_exists_sql(name))

        return self.cursor.fetchone()

    def schema_create(self, schema, owner):
        self.sqls += self.flavor.create_schema_sql(schema, owner)
        self.service_params['schema'] = schema

    def grant_schema_access(self, schema, role):
        pass

    def _get_flavor(self):
        rds = self.ctx.provider.session.client('rds')
        db_instance = rds.describe_db_instances(DBInstanceIdentifier=self.instance)

        engine = next(iter(db_instance.get('DBInstances') or []), {}).get('Engine')
        if engine == 'mysql':
            return MySQLFlavor()
        elif engine == 'postgres':
            return PostgreSQLFlavor()

        raise NotSupportedEngineException()

    def prompt(self):
        queries = highlight("\n".join(self.sqls).replace(self.password, '*' * 8), get_lexer_by_name('sql'),
                            get_formatter_by_name('console'))

        if not click.prompt("Execute: \n" + queries, type=Boolean()):
            click.secho("Aborted!", fg="yellow")
            return False

        return True

    def commit(self):
        for query in self.sqls:
            click.secho(query.replace(self.password, '*' * 8) + '.' * 5, nl=False)
            self.cursor.execute(query)
            click.secho('OK', fg="green")

        return self.service_params


class DBManager(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def initdb(self, instance, db):
        with ExecutionContext(self.ctx, instance) as context:
            if context.db_exists(db):
                logger.error("There is already a db named: '{}'".format(db))
                sys.exit(1)

            context.db_create(db, db)

            if not context.prompt():
                return

            self._write_ssm(
                'resource:{instance}/{db}'.format(instance=instance, db=db),
                context.commit()
            )

    def grant_db_access(self, instance, db):
        with ExecutionContext(self.ctx, instance) as context:
            if not context.db_exists(db):
                logger.error("Unable to grant db permissions to non existing db '{}', use initdb".format(db))
                sys.exit(1)

            role_name = '{service}_service'.format(service=self.ctx.name)

            # @todo - do a proper check if service has an access
            if context.user_exists(role_name):
                logger.error("Service has already an access to '{}'".format(db))
                sys.exit(2)

            context.grant_db_access(role_name, db)

            if not context.prompt():
                return

            self._write_ssm(
                'service:{service}/{instance}/{db}'.format(instance=instance, db=db, service=self.ctx.name),
                context.commit()
            )

    def initschema(self, instance, db, schema):
        with ExecutionContext(self.ctx, instance) as context:
            if not context.flavor.supports_schemas():
                logger.error("Instance {instance} doesn't support schemas".format(instance=instance))
                sys.exit(1)

            if not context.db_exists(db):
                logger.error("Unable to init schema on non existing db '{}', use initdb".format(db))
                sys.exit(2)

            if context.schema_exists(schema):
                logger.error("Schema '{}' already exists".format(db))
                sys.exit(3)

            role_name = 'service_' + self.ctx.name

            context.schema_create(schema, role_name)

            if not context.prompt():
                return

            context.commit()

    def grant_schema_access(self, instance, db, schema):
        with ExecutionContext(self.ctx, instance) as context:
            if not context.flavor.supports_schemas():
                logger.error("Instance {instance} doesn't support schemas".format(instance=instance))
                sys.exit(1)

            if not context.db_exists(db):
                logger.error("Unable to init schema on non existing db '{}', use initdb".format(db))
                sys.exit(2)

            if not context.schema_exists(schema):
                logger.error("Schema '{}' doesn't exists, use initschema".format(schema))
                sys.exit(3)

            context.grant_schema_access(schema, role)

            if not context.prompt():
                return

            self._write_ssm(
                'service:{service}/{instance}/{db}/{schema}'.format(instance=instance, db=db, service=self.ctx.name,
                                                                    schema=schema),
                context.commit()
            )

    def _write_ssm(self, namespace, values):
        ssm = self.ctx.provider.ssm
        for key, value in values.items():
            ssm.write(namespace, key, value, True)
