from __future__ import absolute_import

import glob
import os
import subprocess
from os.path import join, isdir

import click

from stylist.commands.cmd_check import which
from stylist.helper.rds import get_dsn_parameters


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

            service_id, migration_table, db_params, exec_params = get_dsn_parameters(ssm, superuser, instance, db)

            dsn = self._build_dsn(**db_params)

            exec_params.update(ssm.get_parameters('service:' + self.ctx.name))

            self._exec(
                [cmd, '--no-config-file', '-vvvv', '--database', dsn, '--migration-table', migration_table, path],
                exec_params
            )

    def _exec(self, args, env={}):
        click.secho("Executing: " + " ".join([self.cmd] + args), fg="blue")

        p = subprocess.Popen([self.cmd] + args, cwd=self.ctx.working_dir, env=env,
                             stdout=click.get_text_stream("stdout"),
                             stderr=click.get_text_stream("stderr"))
        return p.communicate()
