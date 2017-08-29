import os
from abc import ABCMeta, abstractmethod

import yaml
from os.path import join


class Provider(object):
    __metaclass__ = ABCMeta

    name = None

    def __init__(self, ctx):
        self.ctx = ctx
        self.values = {}

    @property
    def config_path(self):
        return join(self.ctx.profile_dir, "config." + self.name)

    def load(self, path):
        with open(path, "r") as f:
            self.values = yaml.load(f)

    def dump(self, values):
        os.mkdir(self.ctx.profile_dir)

        with open(self.config_path, "w+") as f:
            yaml.dump(values, f)

    def __getattr__(self, item):
        return self.values[item]
