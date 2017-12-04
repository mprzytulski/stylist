import abc


class DBFlavor(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, host, port, user, password, db):
        self.connection = self._connect(host, port, user, password, db)

    @abc.abstractmethod
    def db_exists(self, database_name):
        pass

    @abc.abstractmethod
    def role_exists(self, role_name):
        pass

    @abc.abstractmethod
    def _connect(self, host, port, user, password, db):
        pass

    @abc.abstractmethod
    def get_engine(self):
        pass

    @abc.abstractmethod
    def create_database_queries(self, database_name, role_name):
        pass

    def execute(self, sqls):
        with self.connection.cursor() as cursor:
            if not isinstance(sqls, list):
                sqls = [sqls]

            for sql in sqls:
                cursor.execute(sql)

    def execute_one(self, sql):
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()

    def build_dsn(self, user, password, host, port=5432, db='postgres', schema='public'):
        return '{connection}://{user}:{password}@{host}:{port}/{db}'.format(
            connection=self.get_engine(),
            user=user,
            password=password,
            host=host,
            port=port,
            db=db
        )


class PostgreSQLFlavor(DBFlavor):
    def __init__(self, host, port, user, password, db='template1'):
        super(PostgreSQLFlavor, self).__init__(host, port, user, password, db)

    def get_engine(self):
        return 'postgresql'

    def _connect(self, host, port, user, password, db):
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        dsn = self.build_dsn(user, password, host, port, db, )

        conn = psycopg2.connect(dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        return conn

    def role_exists(self, role_name):
        return self.execute_one(
            "SELECT 1 FROM pg_user WHERE usename = '{role_name}'".format(role_name=role_name)
        )

    def db_exists(self, database_name):
        return self.execute_one(
            "SELECT 1 FROM pg_database WHERE datname='{database_name}'"
                .format(database_name=database_name)
        )

    def create_database_queries(self, database_name, role_name):
        return ['CREATE DATABASE {database_name} OWNER {role_name} ENCODING "UTF-8"'.format(
            database_name=database_name,
            role_name=role_name
        )]

    def create_role_queries(self, role_name, role_password, db_owner=False):
        queries = [
            """CREATE ROLE {role_name} LOGIN PASSWORD '{role_password}'""".format(
                role_name=role_name,
                role_password=role_password
            )
        ]

        if db_owner:
            queries.append("GRANT {role_name} TO postgres".format(role_name=role_name))

        return queries

    def drop_role_queries(self, role_name):
        return [
            'DROP ROLE {role_name}'.format(role_name=role_name)
        ]

    def drop_database_queries(self, database_name):
        return [
            'DROP DATABASE {database_name};'.format(database_name=database_name)
        ]

    def grant_revoke_queries(self, operation, database_name, schema_name, role_name):
        to_from = 'TO' if operation == 'GRANT' else 'FROM'
        return [
            '{operation} ALL PRIVILEGES ON SCHEMA {schema} {to_from} {role_name};'.format(
                operation=operation, schema=schema_name, role_name=role_name, db=database_name, to_from=to_from
            ),

            '{operation} ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema} {to_from} {role_name};'.format(
                operation=operation, schema=schema_name, role_name=role_name, db=database_name, to_from=to_from
            ),
            'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} {operation} ALL PRIVILEGES ON TABLES {to_from} {role_name};'.format(
                operation=operation, schema=schema_name, role_name=role_name, db=database_name, to_from=to_from
            ),

            '{operation} ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {schema} {to_from} {role_name};'.format(
                operation=operation, schema=schema_name, role_name=role_name, db=database_name, to_from=to_from
            ),

            'ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} {operation} ALL PRIVILEGES ON SEQUENCES {to_from} {role_name};'.format(
                operation=operation, schema=schema_name, role_name=role_name, db=database_name, to_from=to_from
            ),
        ]


class MySQLFlavor(DBFlavor):
    def __init__(self, host, port, user, password, db='mysql'):
        super(MySQLFlavor, self).__init__(host, port, user, password, db)

    def get_engine(self):
        return 'mysql+mysqldb'

    def _connect(self, host, port, user, password, db):
        import MySQLdb
        return MySQLdb.connect(host=host, user=user, passwd=password, db=db, port=int(port))

    def role_exists(self, role_name):
        return self.execute_one(
            "SELECT 1 FROM mysql.user WHERE user = '{role_name}'".format(role_name=role_name)
        )

    def db_exists(self, database_name):
        return self.execute_one(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{}'".format(database_name)
        )

    def create_database_queries(self, database_name, role_name):
        return ['CREATE DATABASE {database_name} CHARACTER SET UTF8 COLLATE utf8_bin'.format(
            database_name=database_name,
            role_name=role_name
        )]

    def create_role_queries(self, role_name, role_password, db_owner=False):
        queries = [
            """CREATE USER '{role_name}'@'%' IDENTIFIED BY '{role_password}'""".format(
                role_name=role_name,
                role_password=role_password,
            )
        ]

        if db_owner:
            queries.append(
                "GRANT ALL PRIVILEGES ON {role_name}.* TO '{role_name}'@'%' WITH GRANT OPTION".format(
                    role_name=role_name,
                    role_password=role_password
                )
            )
            queries.append("GRANT SELECT ON mysql.user TO '{role_name}'@'%'".format(role_name=role_name))

        queries.append('FLUSH PRIVILEGES')

        return queries

    def drop_role_queries(self, role_name):
        return [
            "DROP USER '{role_name}'@'%'".format(role_name=role_name)
        ]

    def drop_database_queries(self, database_name):
        return [
            'DROP DATABASE {database_name};'.format(database_name=database_name)
        ]

    def grant_revoke_queries(self, operation, database_name, schema_name, role_name):
        to_from = 'TO' if operation == 'GRANT' else 'FROM'
        return [
            "{operation} ALL PRIVILEGES ON {database_name}.* {to_from} '{role_name}'@'%'".format(
                database_name=database_name,
                operation=operation,
                to_from=to_from,
                role_name=role_name
            )
        ]

    def execute(self, sqls):
        cursor = self.connection.cursor()
        if not isinstance(sqls, list):
            sqls = [sqls]

        for sql in sqls:
            cursor.execute(sql)

    def execute_one(self, sql):
        cursor = self.connection.cursor()
        cursor.execute(sql)
        return cursor.fetchone()
