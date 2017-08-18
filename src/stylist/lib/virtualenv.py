from __future__ import absolute_import

import shutil
import subprocess
import tempfile

from os.path import join, isdir, exists

import click

from stylist.lib.pip import Pip


class VirtualenvException(Exception):
    def __init__(self, message, *args):
        super(VirtualenvException, self).__init__(*args)
        self.message = message


class Virtualenv(object):
    def __init__(self, name, runtime, cleanup=False):
        self.name = name
        self.cleanup = cleanup
        self.runtime = runtime

        self.location = join(tempfile.gettempdir(), "venv-{name}".format(name=self.name))

        self.created = False

        self.pip = Pip(self)

    @property
    def bin_dir(self):
        return join(self.location, "bin")

    def get_executable(self, name):
        return join(self.bin_dir, name)

    def __enter__(self):
        if not isdir(self.location):
            click.secho("Creating temporary virtualenv: {}".format(click.format_filename(self.location)), fg="green")
            self.create()
        else:
            click.secho("Using existing virtualenv", fg="blue")

        return self

    def create(self):
        args = ["virtualenv", "--no-site-packages", "--python=" + self.runtime, self.location]
        popen = subprocess.Popen(args)

        if popen.wait() != 0:
            raise VirtualenvException("Failed to create virtualenv")

        self.created = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.location and exists(self.location) and self.cleanup:
            shutil.rmtree(self.location)

