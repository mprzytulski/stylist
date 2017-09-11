from os.path import join, isfile

import click
from click import style

from stylist.click.types import Boolean
from stylist.feature import Feature
from stylist.wrapper.terraform import Terraform


class DockerFeature(Feature):
    def setup(self, ctx):
        _docker = style('Docker', fg='blue')

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
            'docker/Dockerfile.jinja2': dockerfile
        }

        for src, dst in templates.items():
            dst_path = join(ctx.working_dir, dst)
            if isfile(dst_path):
                continue

            template = self.templates.get_template(src)
            with open(dst_path, 'w+') as f:
                f.write(template.render(**values))

        if click.prompt(_docker + ' | Enable terraform ecs_service support?', type=Boolean(), default='yes'):
            alias = ctx.name

            if dockerfile != 'Dockerfile':
                alias += '-' + dockerfile.replace('Dockerfile.', '')

            self.enable_terraform(ctx, 'ecs_service', alias)
