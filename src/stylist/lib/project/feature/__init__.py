import os
import pkgutil
import importlib
import shutil
from glob import glob

from os.path import join

import hcl
from click import style, prompt


class Feature(object):
    def __init__(self):
        self.templates = None

    def enable_terraform(self, ctx):
        shutil.copytree(join(self.templates.destination, 'terraform'), join(ctx.working_dir, 'terraform'))

    def terraform_install_module(self, ctx, module_name, required=None):
        values = {}
        template = self.templates.get_template('terraform_module.j2')
        for tf_file in glob(join(self.templates.destination, 'terraform_modules', module_name, '*.variables.tf')):
            try:
                with open(tf_file, 'r') as f:
                    variables = hcl.load(f).get("variable")

                for name, config in variables.items():
                    prefix = "{feature}({module}) Enter value for: {variable}".format(
                        feature=style("Terraform", fg="blue"),
                        module=style(module_name, fg="green"),
                        variable=name
                    )
                    values[name] = prompt(prefix, default=config.get("default"))

                rendered = template.render(
                    module_name=module_name,
                    vars=values,
                    source=join(self.templates.destination, 'terraform_modules', module_name)
                )

                with open(join(ctx.working_dir, 'terraform', 'module.' + module_name + '.tf'), 'w+') as f:
                    f.write(rendered)
            except Exception as e:
                raise e
                pass


FEATURES = {}


def get_feature(name):
    return FEATURES.get(name)


pkgpath = os.path.dirname(__file__)
for x, _name, y in pkgutil.iter_modules([pkgpath]):
    try:
        cls = _name.title() + 'Feature'
        _module_name = __name__ + '.' + _name
        m = importlib.import_module(_module_name)
        FEATURES[_name] = getattr(m, cls)()
    except ImportError as e:
        raise e
        pass
