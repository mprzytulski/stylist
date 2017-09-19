from __future__ import absolute_import

import json
import re
import shutil
import subprocess
import sys
import tempfile
from glob import glob
from os.path import isfile, join, isdir, exists

import hcl

import click
from click import style, prompt
from stylist.cli import logger
from stylist.commands.cmd_check import which


class TerraformException(Exception):
    def __init__(self, message):
        self.message = message


class Terraform(object):
    STYLIST_VAR_NAMES = ('aws_region', 'aws_profile', 'aws_account_id', 'environment', 'alb_internal_arn',
                         'alb_external_arn')

    def __init__(self, ctx, templates=None):
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

        aws_session = self.ctx.provider.session

        args += ['-var', '{}={}'.format('aws_account_id', aws_session.client('sts').get_caller_identity()["Account"])]
        args += ['-var', '{}={}'.format('aws_region', aws_session.region_name)]
        args += ['-var', '{}={}'.format('aws_profile', self.ctx.provider.profile)]
        args += ['-var', '{}={}'.format('environment', self.ctx.environment)]

        alb = aws_session.client('elbv2')

        listeners = {}
        for lb in alb.describe_load_balancers().get('LoadBalancers'):
            listeners[lb.get("LoadBalancerName")] = \
                alb.describe_listeners(LoadBalancerArn=lb.get("LoadBalancerArn")).get("Listeners")[0].get("ListenerArn")

        args += ['-var', '{}={}'.format('alb_internal_arn', listeners.get("ecs-internal-lb"))]
        args += ['-var', '{}={}'.format('alb_external_arn', listeners.get("ecs-external-lb"))]

        output = None
        if save:
            f = tempfile.NamedTemporaryFile(prefix="tf-plan.", delete=False)
            f.close()

            args += ['-out=' + f.name]

            output = f.name

        self._exec(args)

        return output

    def apply(self, plan):
        self._ensure_env(get=False)

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
            self._exec(['workspace', 'new', self.ctx.environment])

        self._exec(['workspace', 'select', self.ctx.environment])

        if get:
            self._exec(['init', '-upgrade=true'])

        return vars_file

    def _exec(self, args):
        click.secho("Executing: " + " ".join([self.cmd] + args), fg="blue")

        p = subprocess.Popen([self.cmd] + args, cwd=self.terraform_dir,
                             stdout=click.get_text_stream("stdout"),
                             stderr=click.get_text_stream("stderr"))
        return p.communicate()

    def configure_module(self, module_name, alias):
        maped_values = {
            'name': alias
        }

        values = {}
        current_vars = {}
        template = self.templates.get_template('internal/terraform/module.jinja2')

        module_dir = join(self.templates.destination, 'terraform_modules', module_name)

        if not isdir(module_dir):
            logger.error("Unable to locate '{}' module definition".format(module_name))
            sys.exit(1)

        full_module_name = module_name + '_' + alias

        module_file = join(self.terraform_dir, 'module.' + full_module_name + '.tf')
        if exists(module_file):
            regexp = ur'^\s*(?P<name>\w+)\s*=\s*"?(?P<value>.*?)"?$'

            try:
                with open(module_file, 'r') as f:
                    current_vars = {v.group('name'): v.group('value') for k, v in
                                    enumerate(re.finditer(regexp, f.read(), re.MULTILINE))}

                click.secho("Using existing definition from: '{}'\n".format(
                    module_file.replace(self.terraform_dir + '/', '')
                ), fg='blue')

            except Exception:
                pass

        module_variables = []

        for tf_file in glob(join(module_dir, '*.tf')):
            try:
                with open(tf_file, 'r') as f:
                    variables = hcl.load(f).get("variable")
                    module_variables += variables.keys()

                if not variables:
                    continue

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

                        _val = prompt(prefix, default=current_vars.get(name, config.get("default")))

                        if _val and _val != config.get("default"):
                            values[name] = _val
            except Exception:
                pass

        rendered = template.render(
            module_name=module_name,
            full_module_name=full_module_name,
            vars=values,
            internal=filter(lambda x: unicode(x) in module_variables, Terraform.STYLIST_VAR_NAMES),
            source=self.templates.get_module_source(module_name),
            alias=alias
        )

        with open(module_file, 'w+') as f:
            f.write(rendered)

        click.secho("All done, module file updated: '{}'".format(
            module_file.replace(self.terraform_dir + '/', '')
        ), fg='green')
