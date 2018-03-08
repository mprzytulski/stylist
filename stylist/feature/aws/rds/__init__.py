import click

from stylist.helper.rds.flavors import MySQLFlavor, PostgreSQLFlavor
from stylist.utils import random_password


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
            host=params.get('host'),
            db=db,
            user=params.get('user'),
            password=params.get('password'),
            port=str(params.get('port')),
        )


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

    def build_dsn(self):
        return self.flavor.build_dsn(**self.credentials)

    def _get_flavor(self, instance):
        engine = self.get_instance_type(instance)
        if engine == 'mysql':
            return MySQLFlavor(**self.credentials)
        elif engine == 'postgres':
            return PostgreSQLFlavor(**self.credentials)

        raise NotSupportedEngineException()

    def get_instance_type(self, instance):
        rds = self.ctx.provider.session.client('rds')
        db_instance = rds.describe_db_instances(DBInstanceIdentifier=instance)

        return next(iter(db_instance.get('DBInstances') or []), {}).get('Engine')
