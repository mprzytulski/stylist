from __future__ import absolute_import

import subprocess
from os.path import join, isfile

import click

from stylist.cli import logger


class PipException(Exception):
    pass


class Pip(object):
    def __init__(self, virtualenv):
        self.virtualenv = virtualenv

        self.pip = join(self.virtualenv.bin_dir, "pip")

        if not isfile(self.pip):
            raise PipException("Unable to locate pip executable")

    def install_dependencies(self, dependencies):
        for dependency in dependencies:
            click.secho("Installing dependencies: {}".format(dependency), fg="blue")
            try:
                args = [self.pip, "install"]
                if isfile(dependency):
                    args += ["-r"]

                args += [dependency]

                p = subprocess.Popen(args, stdout=click.get_text_stream("stdout"),
                                     stderr=click.get_text_stream("stderr"))
                out, err = p.communicate()
            except Exception as e:
                logger.exception(e.message)
                raise e

    def list_dependencies(self):
        p = subprocess.Popen([self.pip, "freeze", "-l"], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()

        return out.split("\n")
