from __future__ import absolute_import

import json
import shutil
import subprocess
import tempfile
from glob import glob
from os.path import isfile, join, isdir, exists

import click
import hcl
from click import style, prompt

from stylist.commands.cmd_check import which


class TerraformException(Exception):
    def __init__(self, message):
        self.message = message


class Terraform(object):
    STYLIST_VAR_NAMES = ('aws_region', 'aws_account_id', 'environment')

    def __init__(self, ctx, templates):
        self.ctx = ctx
        self.cmd = which('terraform')
        self.templates = templates

    @property
    def terraform_dir(self):
        return join(self.ctx.working_dir, "terraform")

    def setup(self):
        if not exists(self.terraform_dir):
            shutil.copytree(join(self.templates.destination, 'terraform'), self.terraform_dir)

    def plan(self, save=False):
        vars_file = self._ensure_env()

        args = ['plan', '-var-file', vars_file]

        output = None
        if save:
            f = tempfile.NamedTemporaryFile(prefix="tf-plan.", delete=False)
            f.close()

            args += ['-out=' + f.name]

            output = f.name

        self._exec(args)

        return output

    def apply(self, plan):
        vars_file = self._ensure_env(get=False)

        args = ['apply', plan]

        self._exec(args)

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

    def _ensure_env(self, get=True):
        vars_file = join(self.terraform_dir, 'env.{env}.tfvars'.format(env=self.ctx.environment))

        if not isfile(vars_file):
            raise TerraformException("Missing vars file: " + vars_file)

        if self.ctx.environment == 'local':
            raise TerraformException("You can't use terraform on local env")

        if not isdir(join(self.terraform_dir, 'terraform.tfstate.d', self.ctx.environment)):
            self._exec(['env', 'new', self.ctx.environment])

        self._exec(['env', 'select', self.ctx.environment])

        if get:
            self._exec(['get'])

        return vars_file

    def _exec(self, args):
        p = subprocess.Popen([self.cmd] + args, cwd=self.terraform_dir,
                             stdout=click.get_text_stream("stdout"),
                             stderr=click.get_text_stream("stderr"))
        return p.communicate()

    def configure_module(self, module_name, alias):
        maped_values = {
            'name': alias
        }
        values = {}
        template = self.templates.get_template('internal/terraform/module.jinja2')
        for tf_file in glob(join(self.templates.destination, 'terraform_modules', module_name, '*.variables.tf')):
            try:
                with open(tf_file, 'r') as f:
                    variables = hcl.load(f).get("variable")

                for name, config in variables.items():
                    if name in Terraform.STYLIST_VAR_NAMES:
                        continue

                    if name in maped_values:
                        values[name] = maped_values.get(name)
                    else:
                        prefix = "{feature}({module}) Enter value for: {variable}".format(
                            feature=style("Terraform", fg="blue"),
                            module=style(module_name, fg="green"),
                            variable=name
                        )

                        _val = prompt(prefix, default=config.get("default"))

                        if _val and _val != config.get("default"):
                            values[name] = _val

                rendered = template.render(
                    module_name=module_name,
                    vars=values,
                    internal=Terraform.STYLIST_VAR_NAMES,
                    source=join(self.templates.destination, 'terraform_modules', module_name),
                    alias=alias
                )

                with open(join(self.terraform_dir, 'module.' + module_name + '_' + alias + '.tf'), 'w+') as f:
                    f.write(rendered)
            except Exception as e:
                raise e
                pass
