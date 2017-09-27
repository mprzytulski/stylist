from __future__ import absolute_import

import glob
import os
import subprocess
from os.path import join, isdir

import click
import re

from stylist.commands.cmd_check import which


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
        db = db if not superuser else 'superuser_' + db
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

            superuser = db.startswith('superuser_')
            db = db.replace('superuser_', '')

            db_params = {}

            resource_params_id = '/resource/{instance}/{db}/'.format(instance=instance, db=db)
            resource_id = resource_params_id.replace('/resource/', 'resource:')

            exec_params = {}

            for key, value in ssm.get_parameters(resource_id, env=False).items():
                exec_params[ssm._normalize_name(key, True)] = value
                db_params[key.replace(resource_params_id, '')] = value

            """ If migrations are for different database than master we use service credentials, otherwise use master"""
            if not superuser:
                service_params_id = '/service/{name}/{instance}/{db}/'.format(instance=instance, db=db,
                                                                              name=self.ctx.name)
                service_id = service_params_id.replace('/service/', 'service:')
                migration_table = 'migrations_' + self.ctx.name
            else:
                service_params_id = '/master/{instance}/'.format(instance=instance)
                service_id = service_params_id.replace('/master/', 'master:')
                migration_table = 'migrations_master_' + self.ctx.name

            for key, value in ssm.get_parameters(service_id, env=False).items():
                db_params[key.replace(service_params_id, '')] = value

            migration_table = re.sub('\W', '_', migration_table)

            dsn = self._build_dsn(**db_params)

            exec_params.update(ssm.get_parameters('service:' + self.ctx.name))

            self._exec(
                [cmd, '--no-config-file', '-b', '-v', '--database', dsn, '--migration-table', migration_table, path],
                exec_params
            )

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
