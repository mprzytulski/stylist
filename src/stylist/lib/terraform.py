from __future__ import absolute_import

import json
import subprocess

from os.path import isfile, join, isdir

import click
import hcl

from stylist.commands.cmd_check import which


class TerraformException(Exception):
    def __init__(self, message):
        self.message = message


class Terraform(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.cmd = which('terraform')

    @property
    def terraform_dir(self):
        return join(self.ctx.working_dir, "terraform")

    def plan(self):
        self._ensure_env()

        vars_file = 'env.{env}.tfvars'.format(env=self.ctx.environment)

        if not isfile(vars_file):
            raise TerraformException("Missing vars file: " + vars_file)

        self._exec(['plan', '-var-file', vars_file])

    def sync_vars(self, source_profile, destination_profile):
        source_file = join(self.terraform_dir, 'env.{}.tfvars'.format(source_profile))
        if not isfile(source_file):
            raise TerraformException("Missing tfvars file for source profile: {}".format(source_profile))

        destination_file = join(self.terraform_dir, 'env.{}.tfvars'.format(destination_profile))

        source_vars = self._get_vars(source_file)
        destination_vars = self._get_vars(destination_file)

        # merge values
        for name, val in source_vars.items():
            _default = val if name not in destination_vars else destination_vars.get(name, "")
            prompt = '{name}: "{source_value}" -> "{dest_value}"'.format(
                name=name,
                source_value=val,
                dest_value=destination_vars.get(name, "")
            )
            destination_vars[name] = click.prompt(
                click.style(prompt, fg="yellow" if val != _default else "green"),
                default=_default
            )

        # delete if dest contain var which isn't define in source
        for name, val in destination_vars.items():
            if name in source_vars:
                continue

            prompt = '{name}: "{source_value}" -> "{dest_value}"'.format(
                name=name,
                source_value=val,
                dest_value="[del]"
            )

            _val = click.prompt(
                click.style(prompt, fg="red"),
                default='[del]'
            )

            if _val == '[del]':
                del destination_vars[name]

        with open(destination_file, 'w+') as f:
            for name, value in destination_vars.items():
                f.write("{name} = {value}\n".format(name=name, value=json.dumps(value)))

        click.secho("All done.", fg="green")

    def _get_vars(self, tfvars_file):
        try:
            with open(tfvars_file, 'r') as fp:
                obj = hcl.load(fp)

                return obj
        except Exception:
            return {}

    def _ensure_env(self):
        if self.ctx.environment == 'local':
            raise TerraformException("You can't use terraform on local env")

        if not isdir(join(self.terraform_dir, 'terraform.tfstate.d', self.ctx.environment)):
            self._exec(['env', 'new', self.ctx.environment])

        self._exec(['env', 'select', self.ctx.environment])

    def _exec(self, args):
        p = subprocess.Popen([self.cmd] + args, cwd=self.terraform_dir,
                             stdout=click.get_text_stream("stdout"),
                             stderr=click.get_text_stream("stderr"))
        return p.communicate()

