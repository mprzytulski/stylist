from __future__ import absolute_import

import glob
import os
import subprocess
from os.path import join, isdir

import click
import re

from stylist.commands.cmd_check import which
from stylist.helper.rds import DbContext, get_connection_credentials


class Yoyo(object):
    def __init__(self, ctx):
        self.cmd = which('yoyo')
        self.migrations_dir = join(ctx.working_dir, 'db_migrations')
        self.ctx = ctx

        if not isdir(self.migrations_dir):
            os.mkdir(self.migrations_dir)

    def new_migration(self, instance, db, description):
        migration_path = join(self.migrations_dir, instance, db)

        if not isdir(migration_path):
            os.makedirs(migration_path)

        self._exec(
            ['new', migration_path, '--no-config-file', '-m', description]
        )

    def apply(self, instance, db, revision=None, yoyo_args=None):
        self._run_migration_command('apply', instance, db, revision, yoyo_args)

    def rollback(self, instance, db, revision=None):
        self._run_migration_command('rollback', instance, db, revision)

    def _run_migration_command(self, cmd, instance, db, revision=None, yoyo_args=None):
        migration_path = self.migrations_dir
        if instance:
            migration_path = join(migration_path, instance)

        if instance and db:
            migration_path = join(migration_path, db)

        for path in glob.glob(join(migration_path, '*', '*')):
            click.secho('Running migrations from: {}'.format(click.format_filename(path)))
            instance, db = path.replace(self.migrations_dir, '').strip('/').split('/')
            migration_table = re.sub(ur"\W", "_", 'migrations_' + self.ctx.name)

            with DbContext(self.ctx, instance, get_connection_credentials(self.ctx, instance, db)) as context:
                self._exec([
                        cmd, '--no-config-file', '-vvvv', '--database',
                        context.build_dsn(), '--migration-table', migration_table, path
                    ] + list(yoyo_args) or []
                )

    def _exec(self, args, env=None):
        click.secho("Executing: " + " ".join([self.cmd] + args), fg="blue")

        p = subprocess.Popen([self.cmd] + args, cwd=self.ctx.working_dir, env=env or {},
                             stdout=click.get_text_stream("stdout"),
                             stderr=click.get_text_stream("stderr"))
        return p.communicate()
