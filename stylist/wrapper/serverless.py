import os
import re
from os.path import dirname, isfile, join, realpath

import yaml


class FunctionNotFoundException(Exception):
    def __init__(self, function_name, *args):
        super(FunctionNotFoundException, self).__init__(*args)
        self.message = "Function '{}' was not found in current configuration context.".format(function_name)


class InvalidContextException(Exception):
    pass


class LambdaFunction(object):
    def __init__(self, name, config, parent, ctx):
        """

        :param name:
        :param config:
        :type ctx: Serverless
        """
        self.parent = parent
        self.config = config
        self.name = name
        self.ctx = ctx
        self.function_dir = join(self.parent.service_dir, self.name)
        self.resolver = VariableResolver(self.parent.service_dir, self.ctx.environment)

    def get_runtime(self):
        """
        Get runtime name for service or function if name was provided

        :param function_name:
        :return:
        """
        if "runtime" in self.config:
            return self.config["runtime"]

        return self.parent.get_runtime()

    def get_dependencies(self, dev=True):
        check = [
            join(realpath(join(self.parent.service_dir, self.name)), "requirements.txt"),
        ]

        if dev:
            check.append(join(realpath(join(self.parent.service_dir, self.name)), "requirements-dev.txt"))

        return self.parent.get_global_dependencies(dev) + [path for path in check if isfile(path)]

    def get_environment(self):
        env = self.parent.get_environment()
        env.update(
            self.config.get("environment", {})
        )

        return {k: self.resolver.resolve(v) for k, v in env.items()}

    @property
    def handler(self):
        return self.config.get("handler")

    @property
    def global_id(self):
        return self.parent.name + "-" + self.name


class Serverless(object):
    def __init__(self, config, ctx):
        self.ctx = ctx
        with open(config, "r") as f:
            self.config = yaml.load(f)

        self.service_dir = dirname(config)

    @property
    def name(self):
        return self.config["service"] if isinstance(self.config["service"], str) else self.config["service"]["name"]

    def has_function(self, function_name):
        """
        Check if there is a definition for function with given name in serverless.yml configuration

        :param function_name:
        :return:
        """
        return function_name in self.config["functions"]

    def ensure_function(self, function_name):
        if function_name not in self.config["functions"]:
            raise FunctionNotFoundException(function_name)

        return True

    @property
    def functions(self):
        return self.config.get("functions", {})

    def get_runtime(self):
        return self.config["provider"]["runtime"]

    def get_function(self, function_name):
        return LambdaFunction(function_name, self.config["functions"][function_name], self, self.ctx)

    def get_environment(self):
        return self.config.get("provider", {}).get("environment", {})

    def get_global_dependencies(self, dev=False):
        check = [
            join(realpath(join(self.service_dir, "..")), "requirements.txt"),
            join(self.service_dir, 'requirements.txt'),
        ]

        if dev:
            check += [
                join(realpath(join(self.service_dir, "..")), "requirements-dev.txt"),
                join(self.service_dir, 'requirements-dev.txt'),
            ]

        return [path for path in check if isfile(path)]

    @staticmethod
    def from_context(ctx):
        configs = filter(
            lambda x: isfile(x),
            [join(ctx.working_dir, "serverless.yml"), join(os.getcwd(), "serverless.yml")]
        )

        if not len(configs):
            raise InvalidContextException()

        return Serverless(configs.pop(), ctx)


class VariableResolver(object):
    def __init__(self, function_dir, stage):
        super(VariableResolver, self).__init__()
        self.stage = stage
        self.files = {}
        self.function_dir = function_dir

    def resolve(self, value):
        matches = re.search(r"\$\{file\((?P<file>.*?)\):(?P<var>.*?)\}", value)
        if not matches:
            return value

        return self.from_file(matches.group("file"), matches.group("var"))

    def from_file(self, file, var):
        path = realpath(join(self.function_dir, file)).replace("${opt:stage}", self.stage)

        if path not in self.files:
            with open(path, "r") as vars:
                self.files[path] = yaml.load(vars)

        return str(self.files[path].get(var, None))
