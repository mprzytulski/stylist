from dependency_injector import providers
from os.path import join, isfile

import click
from click import style

from stylist.click.types import Boolean
from stylist.feature import Feature
from stylist.feature.docker.lib import Docker


class DockerFeature(Feature):
    """
    Build and manage your docker containers.
    """

    @property
    def installed(self):
        return isfile(join(self.stylist.working_dir, 'Dockerfile'))

    def on_config(self, stylist):
        stylist.main.docker = providers.Factory(
            Docker, stylist=stylist
        )

    def __call__(self, subproject, *args, **kwargs):
        return self.stylist.main.docker()

        # path =
        # docker_files = glob.glob('{}/Dockerfile*'.format(path))
        #
        # if ask:
        #     return _ask_about_docker_files('Which docker file would you like to build?', docker_files)
        # else:
        #     return docker_files


















    def _do_setup(self, init_args):
        _docker = style('Docker', fg='blue')

        prompts = {
            "base_image": {"text": "Docker base image", "default": "python:3-stretch"},
        }

        dockerfile = "Dockerfile"
        while isfile(join(self.stylist.working_dir, dockerfile)):
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
            dst_path = join(self.stylist.working_dir, dst)
            if isfile(dst_path):
                continue

            template = self.templates.get_template(src)
            with open(dst_path, 'w+') as f:
                f.write(template.render(**values))

        if click.prompt(_docker + ' | Enable terraform ecs_service support?', type=Boolean(), default='yes'):
            alias = self.stylist.name

            if dockerfile != 'Dockerfile':
                alias += '-' + dockerfile.replace('Dockerfile.', '')

            self.enable_terraform(self.stylist, 'ecs_service', alias)


