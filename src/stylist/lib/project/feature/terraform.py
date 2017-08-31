import shutil
from glob import glob

from os.path import join, basename

import click
import hcl
from click import style
from jinja2 import Environment, PackageLoader

from stylist.lib.click.types import Boolean
from stylist.lib.project.feature import Feature


class TerraformFeature(Feature):
    TEMPLATES = {
        "provider.tf": ''
    }

    def __init__(self):
        self.templates = Environment(
            loader=PackageLoader(__name__, 'templates'),
        )

    def setup(self, ctx, templates):
        modules = {}
        for dst in glob(join(templates.destination, 'terraform_modules', '*')):
            name = basename(dst)
            prompt = style("Terraform", fg="blue") + " | Enable {} module".format(style(name, fg="green"))
            modules[name] = click.prompt(prompt, type=Boolean(), default='no')

        self.install_base(ctx, templates)
        self.install_modules(ctx, templates, modules)

    def install_base(self, ctx, templates):
        # shutil.copytree(join(templates.destination, 'terraform'), join(ctx.working_dir, 'terraform'))
        pass

    def install_modules(self, ctx, templates, modules):
        for module_name in modules:
            self.install_module(ctx, templates, module_name)

    def install_module(self, ctx, templates, module_name):
        values = {}
        template = self.templates.get_template('terraform_module.j2')
        for tf_file in glob(join(templates.destination, 'terraform_modules', module_name, '*.variables.tf')):
            try:
                with open(tf_file, 'r') as f:
                    variables = hcl.load(f).get("variable")

                for name, config in variables.items():
                    prefix = "{feature}({module}) Enter value for: {variable}".format(
                        feature=style("Terraform", fg="blue"),
                        module=style(module_name, fg="green"),
                        variable=name
                    )
                    values[name] = click.prompt(prefix, default=config.get("default"))

                rendered = template.render(
                    module_name=module_name,
                    vars=values,
                    source=join(templates.destination, 'terraform_modules', module_name)
                )

                with open(join(ctx.working_dir, 'terraform', 'module.' + module_name + '.tf'), 'w+') as f:
                    f.write(rendered)
            except Exception as e:
                raise e
                pass

