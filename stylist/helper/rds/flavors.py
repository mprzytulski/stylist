import abc


class DBFlavor(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def create_db_sql(self, name, encoding, owner):
        pass

    @abc.abstractmethod
    def db_exists_sql(self, name):
        pass

    @abc.abstractmethod
    def create_user_sql(self, role_name, password):
        pass

    @abc.abstractmethod
    def user_exists_sql(self, role_name):
        pass

    @abc.abstractmethod
    def grant_permission_sql(self, user, db):
        pass

    @abc.abstractmethod
    def get_connection_schema(self):
        pass

    @abc.abstractmethod
    def get_connection_db(self):
        pass

    @abc.abstractmethod
    def get_connection(self, user, password, host, port, db, schema=''):
        pass

    def build_dsn(self, user, password, host, port=5432, db='postgres', schema='public'):
        return '{connection}://{user}:{password}@{host}:{port}/{db}'.format(
            connection=self.get_connection_schema(),
            user=user,
            password=password,
            host=host,
            port=port,
            db=db
        )

    def supports_schemas(self):
        return False


class MySQLFlavor(DBFlavor):
    def get_connection_db(self):
        return 'mysql'

    def get_connection_schema(self):
        return 'mysql+mysqldb'

    def db_exists_sql(self, name):
        return "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{}'".format(name)

    def create_user_sql(self, role_name, password):
        return [
            "CREATE USER '{role_name}'@'%' IDENTIFIED BY '{password}';".format(
                role_name=role_name,
                password=password
            )
        ]

    def user_exists_sql(self, role_name):
        return "SELECT 1 FROM mysql.user WHERE user = 'role_name'".format(role_name=role_name)

    def grant_permission_sql(self, user, db):
        return [
            "GRANT ALL ON {db}.* TO '{user}'@'%';".format(
                db=db,
                user=user
            ),
            "FLUSH PRIVILEGES;"
        ]

    def create_db_sql(self, name, encoding, owner):
        return [
            'CREATE DATABASE {db}'.format(db=name)
        ]

    def get_connection(self, user, password, host, port, db, schema=''):
        import MySQLdb
        return MySQLdb.connect(host=host, user=user, passwd=password, db=db, port=int(port))


class PostgreSQLFlavor(DBFlavor):
    def get_connection(self, user, password, host, port, db, schema=''):
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

        dsn = self.build_dsn(user, password, host, port, db, schema)

        conn = psycopg2.connect(dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        return conn

    def get_connection_db(self):
        return 'template1'

    def get_connection_schema(self):
        return 'postgresql'

    def db_exists_sql(self, name):
        return "SELECT 1 FROM pg_database WHERE datname='{}'".format(name)

    def create_user_sql(self, role_name, password):
        return [
            """CREATE ROLE {role_name} LOGIN PASSWORD '{role_password}'""".format(
                role_name=role_name,
                role_password=password
            ),
            "GRANT {role_name} TO postgres".format(role_name=role_name)
        ]

    def user_exists_sql(self, role_name):
        return "SELECT 1 FROM pg_user WHERE usename = '{role_name}'".format(role_name=role_name)

    def grant_permission_sql(self, user, db):
        return []

    def create_db_sql(self, name, encoding, owner):
        return ['CREATE DATABASE {db} OWNER {role_name} ENCODING "UTF-8"'.format(
            db=name,
            role_name=owner
        )]

    def supports_schemas(self):
        return True

    def create_schema_sql(self, name, owner):
        return ['CREATE SCHEMA {schema} AUTHORIZATION {role_name}'.format(
            schema=name,
            role_name=owner
        )]

    def schema_exists_sql(self, name):
        return "SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{}';".format(name)
