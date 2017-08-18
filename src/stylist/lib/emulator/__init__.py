import json
import subprocess
from os.path import join, realpath, dirname

import click

from stylist.lib.emulator.aws import Emulator
from stylist.lib.utils import colourize, highlight_json


class ExecutionContext(object):
    def __init__(self, venv, environment, lambda_function):
        self.environment = environment
        self.lambda_function = lambda_function
        self.venv = venv

        self._generate_wrapper()

    @property
    def environment_variables(self):
        env_vars = self.lambda_function.get_environment()
        env_vars["SENTRY_ENABLED"] = "false"

        return env_vars

    @property
    def details(self):
        return [
            ["ENVIRONMENT", colourize(self.environment)],
            ["VIRTUALENV", self.venv.location],
            ["NEW VIRUTALENV", self.venv.created],
            ["DEPENDENCIES", ", ".join(self.venv.pip.list_dependencies())],
            ["RUNTIME", self.lambda_function.get_runtime()],
        ]

    def _generate_wrapper(self):
        click.secho("Creating execution wrapper")

        handler_module, handler_function = self.lambda_function.handler.split(".")

        with open(join(self.venv.location, "wrapper.py"), "w+") as wrapper:
            wrapper.write(WRAPPER_TEMPLATE.format(
                module=handler_module,
                handler=handler_function,
                function_dir=self.lambda_function.function_dir,
                stylist_lib_dir=realpath(join(dirname(__file__), "../../../"))
            ))

    def execute(self, data):
        p = subprocess.Popen(
            [self.venv.get_executable("python"), "wrapper.py"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            cwd=self.venv.location,
            env=self.environment_variables
        )
        p.stdin.write(data)
        stdout, stderr = p.communicate()

        return ExecutionResult(stdout, stderr)


class ExecutionResult(object):
    def __init__(self, stdout, stderr):
        self.stderr = stderr
        self._stdout = stdout

        try:
            self.obj = json.loads(self._stdout)
        except ValueError:
            self.obj = {}

    @property
    def stdout(self):
        return self.obj.get("result", "")

    @property
    def events(self):
        rows = []

        for module, functions in self.obj.get("events", {}).items():
            for function, calls in functions.items():
                for call in calls:
                    rows.append([module, function, highlight_json(json.dumps(call))])

        return rows

    @property
    def stats(self):
        return self.obj.get("stats", {})


WRAPPER_TEMPLATE = """
# vim:fileencoding=utf-8
# This file is generated on the fly
import os
import sys
import json

root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path[0:0] = ["{function_dir}"]
sys.path.append("{stylist_lib_dir}")

from stylist.lib.wrapper import execute

raw_event = json.load(sys.stdin)

def get_handler():
    import {module}
    from {module} import {handler} as real_handler

    return real_handler, {module}

execute(get_handler, raw_event, {{}})
"""
