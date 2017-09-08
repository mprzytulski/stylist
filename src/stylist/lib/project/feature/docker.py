from os.path import join, isfile

import click
from click import style
from jinja2 import Environment, FileSystemLoader

from stylist.lib.click.types import Boolean
from stylist.lib.project.feature import Feature


class DockerFeature(Feature):
    def setup(self, ctx, templates):
        self.templates = Environment(loader=FileSystemLoader(templates.destination))

        _docker = style('Docker', fg='blue')

        terraform_support = click.prompt(
            _docker + ' | Enable terraform support?',
            type=Boolean(), default='yes'
        )

        prompts = {
            "base_image": {"text": "Docker base image", "default": "python:3-stretch"},
        }

        dockerfile = "Dockerfile"
        while isfile(join(ctx.working_dir, dockerfile)):
            dockerfile = \
                click.prompt("{file} exits, please provide alternative name".format(file=style(dockerfile, fg="red")))

        values = {}
        for name, params in prompts.items():
            params["text"] = '{prefix} | {text}'.format(prefix=_docker, text=params.get("text"))
            values[name] = click.prompt(**params)

        templates = {
            'docker/Dockerfile.jinja2': dockerfile,
            'docker/entrypoint.sh': 'entrypoint.sh'
        }

        for src, dst in templates.items():
            dst_path = join(ctx.working_dir, dst)
            if isfile(dst_path):
                continue

            template = self.templates.get_template(src)
            with open(dst_path, 'w+') as f:
                f.write(template.render(**values))

        if terraform_support:
            self.enable_terraform(ctx)

    def enable_terraform(self, ctx):
        self.enable_terraform(ctx)
        self.terraform_install_module(ctx, 'ecs_service')
