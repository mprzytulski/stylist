import click

from stylist.helper.rds.flavors import MySQLFlavor, PostgreSQLFlavor
from stylist.utils import random_password


class NotSupportedEngineException(Exception):
    pass


class DbContext(object):
    def __init__(self, ctx, instance, credentials):
        self.ctx = ctx
        self.instance = instance
        self.credentials = credentials
        self.queries = []
        self.parameters = {}

    def __enter__(self):
        """
        :rtype DbContext
        :return:
        """
        self.flavor = self._get_flavor(self.instance)
        self.parameters.update(dict(
            host=self.credentials.get('host'),
            port=self.credentials.get('port'),
            instance=self.instance
        ))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.queries = []
        self.parameters = []

    def run_queries(self, sql):
        pass

    def role_exists(self, role_name):
        return self.flavor.role_exists(role_name)

    def db_exists(self, database_name):
        return self.flavor.db_exists(database_name)

    def create_database(self, database_name, role_name):
        self.parameters.update(dict(
            db=database_name,
            owner=role_name
        ))
        self.queries += self.flavor.create_database_queries(database_name, role_name)

        return database_name, role_name

    def create_role(self, role_name, db_owner=True):
        password = random_password()
        self.parameters.update(dict(
            user=role_name,
            password=password
        ))
        self.queries += self.flavor.create_role_queries(role_name, password, db_owner)

        return role_name, password

    def drop_role(self, role_name):
        self.queries += self.flavor.drop_role_queries(role_name)

    def drop_database(self, database_name):
        self.queries += self.flavor.drop_database_queries(database_name)

    def grant_database_access(self, database_name, role_name):
        return self.grant_schema_access(database_name, 'public', role_name)

    def grant_schema_access(self, database_name, schema_name, role_name):
        self.parameters['schema'] = schema_name

        self.queries += self.flavor.grant_revoke_queries('GRANT', database_name, schema_name, role_name)

    def revoke_database_access(self, database_name, role_name):
        return self.revoke_schema_access(database_name, 'public', role_name)

    def revoke_schema_access(self, database_name, schema_name, role_name):
        self.parameters['schema'] = schema_name

        self.queries += self.flavor.grant_revoke_queries('REVOKE', database_name, schema_name, role_name)

    def commit(self):
        for query in self.queries:
            click.secho(query.replace(self.parameters.get('password', '-dummy-'), '*' * 8) + '.' * 5, nl=False)
            self.flavor.execute(
                query
            )
            click.secho('OK', fg="green")

        return self.parameters

    def _get_flavor(self, instance):
        rds = self.ctx.provider.session.client('rds')
        db_instance = rds.describe_db_instances(DBInstanceIdentifier=instance)

        engine = next(iter(db_instance.get('DBInstances') or []), {}).get('Engine')
        if engine == 'mysql':
            return MySQLFlavor(**self.credentials)
        elif engine == 'postgres':
            return PostgreSQLFlavor(**self.credentials)

        raise NotSupportedEngineException()

    def _get_connection_params(self, params):
        return dict(
            host=params.get('host'),
            port=params.get('port'),
            db=params.get('db'),
            user=params.get('user'),
            password=params.get('password'),
        )
