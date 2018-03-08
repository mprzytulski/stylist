from __future__ import absolute_import

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from glob import glob
from os.path import isfile, join, isdir, exists, basename

import click
import hcl
from click import style, prompt
from jinja2 import Template

from stylist.commands.cmd_check import which
from stylist.utils import compare_dicts

PROVIDER_TEMPLATE = """
provider "aws" {
  region = "${var.context["aws_region"]}"
  profile = "${var.context["aws_profile"]}"
}

variable "context" {
  type = "map"
  default = {}
}
"""


class TerraformException(Exception):
    def __init__(self, message, errno=None):
        self.message = message
        self.errno = errno


class Terraform(object):
    STYLIST_VAR_NAMES = ('context',)

    def __init__(self, stylist, templates=None):
        """
        :param stylist: Stylist
        :param templates:
        """
        self.stylist = stylist
        self.cmd = which('terraform')
        self.templates = templates

    @property
    def terraform_dir(self):
        return join(self.stylist.working_dir, "terraform")

    @property
    def tfupdate_path(self):
        return join(self.terraform_dir, '.tfupdate')

    @property
    def env_vars_file(self):
        return join(self.terraform_dir, 'env.{}.tfvars'.format(self.stylist.environment))

    def plan(self, save=False, force_update=False):
        vars_file = self._ensure_env()
        self._update_modules(force_update)

        args = ['plan']

        if isfile(vars_file):
            args += ['-var-file', vars_file]

        aws_session = self.stylist.provider.session
        alb = aws_session.client('elbv2')

        inject_vars = {
            'aws_account_id': self.stylist.provider.account_id,
            'aws_region': aws_session.region_name,
            'aws_profile': self.stylist.provider.profile,
            'environment': self.stylist.environment,
            'project_name': self.stylist.name
        }

        for lb in alb.describe_load_balancers().get('LoadBalancers'):
            for listener in alb.describe_listeners(LoadBalancerArn=lb.get("LoadBalancerArn")).get("Listeners"):
                key = "alb_{}_arn_{}".format(lb.get("LoadBalancerName"), listener.get("Protocol").lower())
                inject_vars[key] = listener.get("ListenerArn")

        for api in aws_session.client('apigateway').get_rest_apis(limit=200).get('items'):
            inject_vars['api_{}'.format(api.get('name'))] = api.get('id')

        params = []
        for k, v in inject_vars.items():
            params += ['{k}="{v}"'.format(k=k, v=v)]

        args += ['--var', 'context={%s}' % ", ".join(params)]

        output = None
        if save:
            f = tempfile.NamedTemporaryFile(prefix="tf-plan.", delete=False)
            f.close()

            args += ['-out=' + f.name]

            output = f.name

        self.setup()

        return output, self._exec(args)

    def apply(self, plan):
        self._ensure_env()

        args = ['apply', plan]

        return self._exec(args)

    def sync_vars(self, source_profile, destination_profile):
        source_file = join(self.terraform_dir, 'env.{}.tfvars'.format(source_profile))
        if not isfile(source_file):
            raise TerraformException("Missing tfvars file for source profile: {}".format(source_profile), 1)

        destination_file = join(self.terraform_dir, 'env.{}.tfvars'.format(destination_profile))

        destination_vars = compare_dicts(self._get_vars(source_file), self._get_vars(destination_file))

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
        vars_file = join(self.terraform_dir, 'env.{env}.tfvars'.format(env=self.stylist.environment))

        if self.stylist.environment == 'local':
            raise TerraformException("You can't use terraform on local env")

        if not isdir(join(self.terraform_dir, 'terraform.tfstate.d', self.stylist.environment)):
            self._exec(['workspace', 'new', self.stylist.environment])

        self._exec(['workspace', 'select', self.stylist.environment])

        return vars_file

    def _update_modules(self, force=False):
        last_update = os.path.getmtime(self.tfupdate_path) if isfile(self.tfupdate_path) else 0

        if force or int(last_update) < int(time.time()) - 3600:
            self._exec(['init', '--upgrade=true'])
            with open(self.tfupdate_path, 'w+') as f:
                f.write(str(int(time.time())))

    def _exec(self, args):
        click.secho("Executing: " + " ".join([self.cmd] + args), fg="blue")

        p = subprocess.Popen([self.cmd] + args, cwd=self.terraform_dir,
                             stdout=click.get_text_stream("stdout"),
                             stderr=click.get_text_stream("stderr"))
        p.communicate()

        return p.returncode

    def configure_module(self, module_name, alias):
        self.setup()
        maped_values = {
            'name': alias
        }

        values = {}
        current_vars = {}
        template = self.templates.get_template('terraform/module.jinja2')

        module_dir = join(self.templates.terraform_local_modules_source, module_name)

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
                    variables = hcl.load(f).get("variable") or {}
                    module_variables += variables.keys()

                if not variables:
                    continue

                for name, config in {k: v for k, v in variables.items() if
                                     k not in Terraform.STYLIST_VAR_NAMES}.items():
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
            except Exception as e:
                print "Error: {}".format(e)

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

    def get_env_vars(self):
        return self._get_vars(self.env_vars_file)

    def dump_env_vars(self, params):
        with open(self.env_vars_file, 'w+') as f:
            for k, v in params.items():
                f.write("{} = \"{}\"\n".format(k, v))

    def setup(self):
        provider_file = join(self.terraform_dir, 'provider.tf')

        if not isdir(self.terraform_dir):
            os.makedirs(self.terraform_dir)

        with open(provider_file, 'w+') as f:
            template = Template(PROVIDER_TEMPLATE)
            f.write(template.render())

        if not isfile(join(self.terraform_dir, 'variables.tf')):
            open(join(self.terraform_dir, 'variables.tf'), 'a').close()

    def list_modules(self):
        modules = {}

        for module in glob(self.templates.terraform_local_modules_source + '/*'):
            with open(join(module, 'module.tf'), 'r') as f:
                line = f.readline().strip()

            modules[basename(module)] = line.replace('## Desc:', '') if line.startswith('## Desc:') else ''

        return modules
