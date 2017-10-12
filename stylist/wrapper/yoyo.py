from __future__ import absolute_import

import glob
import os
import re
import subprocess
import sys
from os.path import join, isdir

import click
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from stylist.cli import logger
from stylist.click.types import Boolean
from stylist.commands.cmd_check import which
from stylist.utils import random_password


class PipException(Exception):
    pass


class Yoyo(object):
    def __init__(self, ctx):
        self.cmd = which('yoyo')
        self.migrations_dir = join(ctx.working_dir, 'db_migrations')
        self.ctx = ctx

        if not isdir(self.migrations_dir):
            os.mkdir(self.migrations_dir)

    def new_migration(self, instance, db, superuser, description):
        db = db if not superuser else '_superuser_' + db
        migration_path = join(self.migrations_dir, instance, db)

        if not isdir(migration_path):
            os.makedirs(migration_path)

        self._exec(
            ['new', migration_path, '--no-config-file', '-m', description]
        )

    def apply(self, instance, db, revision=None):
        self._run_migration_command('apply', instance, db, revision)

    def rollback(self, instance, db, revision=None):
        self._run_migration_command('rollback', instance, db, revision)

    def initdb(self, instance, db):
        ssm = self.ctx.provider.ssm

        params = ssm.get_short_parameters('master:{}'.format(instance))
        params['db'] = 'template1'

        dsn = self._build_dsn(**params)
        conn = psycopg2.connect(dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        sqls = []
        passwd = random_password()

        with conn.cursor() as cur:
            sql = "SELECT 1 FROM pg_database WHERE datname='{}'".format(db)
            cur.execute(sql)
            if cur.fetchone():
                logger.error("There is already a db named: '{}'".format(db))
                sys.exit(1)

            sql = "SELECT 1 FROM pg_user WHERE usename = '{}'".format(db)
            cur.execute(sql)

            if not cur.fetchone():
                sqls.append("""CREATE ROLE {role_name} LOGIN PASSWORD '{role_password}'""".format(
                    role_name=db,
                    role_password=passwd
                ))

                sqls.append("GRANT {role_name} TO postgres".format(role_name=db))

            sqls.append('CREATE DATABASE {db} OWNER {role_name} ENCODING "UTF-8"'.format(
                db=db,
                role_name=db
            ))

            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import get_formatter_by_name

            queries = highlight("\n".join(sqls).replace(passwd, '*' * 8), get_lexer_by_name('sql'),
                                get_formatter_by_name('console'))

            if not click.prompt("Execute: \n" + queries, type=Boolean()):
                click.secho("Aborted!", fg="yellow")

            for query in sqls:
                click.secho(query.replace(passwd, '*' * 8) + '.' * 5, nl=False)
                cur.execute(query)
                click.secho('OK', fg="green")

        namespace = 'resource:{instance}/{db}'.format(instance=instance, db=db)
        ssm.write(namespace, 'db', db, True)
        ssm.write(namespace, 'host', params['host'], True)
        ssm.write(namespace, 'port', params['port'], True)
        ssm.write(namespace, 'user', db, True)
        ssm.write(namespace, 'password', passwd, True)

    def initschema(self, instance, db, schema):
        ssm = self.ctx.provider.ssm

        resource = 'master:{instance}'.format(instance=instance, db=db)
        params = ssm.get_short_parameters(resource)

        if not params:
            logger.error("Unable to locate resource connection settings for: '{}'".format(resource))
            sys.exit(1)

        dsn = self._build_dsn(**params)
        conn = psycopg2.connect(dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        sqls = []
        passwd = random_password()

        with conn.cursor() as cur:
            role_name = 'service_' + schema

            sql = "SELECT 1 FROM pg_user WHERE usename = '{role_name}'".format(role_name=role_name)
            cur.execute(sql)

            if not cur.fetchone():
                sqls.append("""CREATE ROLE {role_name} LOGIN PASSWORD '{role_password}'""".format(
                    role_name=role_name,
                    role_password=passwd
                ))

                sqls.append("GRANT {role_name} TO {db}".format(role_name=role_name, db=db))
                sqls.append(
                    "GRANT {role_name} TO {master_user}".format(role_name=role_name, master_user=params['user']))

                sqls.append("ALTER USER {role_name} SET search_path to {schema};".format(
                    role_name=role_name,
                    schema=schema
                ))

        conn.close()

        resource = 'resource:{instance}/{db}'.format(instance=instance, db=db)
        params = ssm.get_short_parameters(resource)

        if not params:
            logger.error("Unable to locate resource connection settings for: '{}'".format(resource))
            sys.exit(1)

        dsn = self._build_dsn(**params)
        conn = psycopg2.connect(dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cur:
            sql = "SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{}';".format(schema)
            cur.execute(sql)
            if cur.fetchone():
                logger.error("There is already schema named: '{}' in db '{}'".format(schema, db))
                sys.exit(1)

            sqls.append('CREATE SCHEMA {schema} AUTHORIZATION {role_name}'.format(
                schema=schema,
                role_name=role_name
            ))

            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import get_formatter_by_name

            queries = highlight("\n".join(sqls).replace(passwd, '*' * 8), get_lexer_by_name('sql'),
                                get_formatter_by_name('console'))

            if not click.prompt("Execute: \n" + queries, type=Boolean()):
                click.secho("Aborted!", fg="yellow")

            for query in sqls:
                click.secho(query.replace(passwd, '*' * 8) + '.' * 5, nl=False)
                cur.execute(query)
                click.secho('OK', fg="green")

        namespace = 'service:'.format(instance=instance, db=db)
        ssm.write(namespace, 'db', db, True)
        ssm.write(namespace, 'host', params['host'], True)
        ssm.write(namespace, 'port', params['port'], True)
        ssm.write(namespace, 'user', db, True)
        ssm.write(namespace, 'password', passwd, True)

    def grant(self, instance, service, db):
        pass

    def _run_migration_command(self, cmd, instance, db, revision=None):
        migration_path = self.migrations_dir
        if instance:
            migration_path = join(migration_path, instance)

        if instance and db:
            migration_path = join(migration_path, db)

        ssm = self.ctx.provider.ssm

        for path in glob.glob(join(migration_path, '*', '*')):
            click.secho('Running migrations from: {}'.format(click.format_filename(path)))
            instance, db = path.replace(self.migrations_dir, '').strip('/').split('/')

            superuser = db.startswith('_superuser_')
            db = db.replace('_superuser_', '')

            service_id, migration_table, db_params, exec_params = self._get_dsn_parameters(ssm, superuser, instance, db)

            dsn = self._build_dsn(**db_params)

            exec_params.update(ssm.get_parameters('service:' + self.ctx.name))

            self._exec(
                [cmd, '--no-config-file', '-vvvv', '--database', dsn, '--migration-table', migration_table, path],
                exec_params
            )

    def _get_dsn_parameters(self, ssm, superuser, instance, db):
        resource_params_id = '/resource/{instance}/{db}/'.format(instance=instance, db=db)
        resource_id = resource_params_id.replace('/resource/', 'resource:')

        """ If migrations are for different database than master we use service credentials, otherwise use master"""
        if not superuser:
            service_params_id = '/service/{name}/{instance}/{db}/'.format(instance=instance, db=db,
                                                                          name=self.ctx.name)
            service_id = service_params_id.replace('/service/', 'service:')
            migration_table = 'migrations_' + self.ctx.name
        else:
            service_params_id = '/master/{instance}/'.format(instance=instance)
            service_id = service_params_id.replace('/master/', 'master:')
            migration_table = 'migrations_superuser_' + self.ctx.name

        db_params = {}
        exec_params = {}

        for key, value in ssm.get_parameters(service_id, env=False).items():
            db_params[key.replace(service_params_id, '')] = value

        for key, value in ssm.get_parameters(resource_id, env=False).items():
            exec_params[ssm._normalize_name(key, True)] = value
            db_params[key.replace(resource_params_id, '')] = value

        migration_table = re.sub('\W', '_', migration_table)

        return service_id, migration_table, db_params, exec_params

    def _exec(self, args, env={}):
        click.secho("Executing: " + " ".join([self.cmd] + args), fg="blue")

        p = subprocess.Popen([self.cmd] + args, cwd=self.ctx.working_dir, env=env,
                             stdout=click.get_text_stream("stdout"),
                             stderr=click.get_text_stream("stderr"))
        return p.communicate()

    def _build_dsn(self, user, password, host, port=5432, db='postgres', schema='public'):
        return 'postgresql://{user}:{password}@{host}:{port}/{db}'.format(
            user=user,
            password=password,
            host=host,
            port=port,
            db=db
        )
