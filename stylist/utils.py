from __future__ import absolute_import

import json
import os
import random
import string
from textwrap import wrap

import sys
import click
import math
from pygments import highlight, lexers, formatters
from terminaltables import SingleTable

from stylist.click.types import Boolean


def colourize(name):
    if name in ["prod", "production"]:
        return click.style(name, fg="red")
    elif name in ["uat", "preprod"]:
        return click.style(name, fg="yellow")
    elif name in ["staging"]:
        return name
    else:
        return click.style(name, fg="green")


def highlight_json(text, format=False):
    if format:
        if isinstance(text, str):
            text = json.load(text)

        text = json.dumps(text, sort_keys=True, indent=4)

    if isinstance(text, (dict, list)):
        text = json.dumps(text)

    return highlight(
        unicode(text, 'UTF-8'),
        lexers.JsonLexer(),
        formatters.TerminalFormatter()
    )


def table(title, data, headers=None, wraped_col=1):
    if not headers:
        headers = ["Name", "Value"]

    map(
        lambda x: click.style(x, fg="blue"),
        headers
    )

    if isinstance(data, dict):
        data = [[k, v] for k, v in data.items()]

    _data = [headers] + data

    _table = SingleTable(_data, click.style(title, fg="blue"))
    _table.inner_row_border = True

    max_width = math.fabs(_table.column_max_width(wraped_col)) or 30
    for i, val in enumerate(_data):
        wrapped_string = '\n'.join(wrap(str(val[wraped_col]), max_width))
        _table.table_data[i][wraped_col] = wrapped_string

    return _table


def display_section(title, data, title_fg="blue", body_fg="white"):
    click.secho(title.upper() + ": ", fg=title_fg)

    click.secho(data + "\n", fg=body_fg)


def line_prefix(ctx):
    return "[{env}] ".format(env=colourize(ctx.environment))


def _walk_to_root(path):
    """
    Yield directories starting from the given directory up to the root
    """
    if not os.path.exists(path):
        raise IOError('Starting path not found')

    if os.path.isfile(path):
        path = os.path.dirname(path)

    last_dir = None
    current_dir = os.path.abspath(path)
    while last_dir != current_dir:
        yield current_dir
        parent_dir = os.path.abspath(os.path.join(current_dir, os.path.pardir))
        last_dir, current_dir = current_dir, parent_dir


def find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=False, path=None):
    """
    Search in increasingly higher folders for the given file
    Returns path to the file if found, or an empty string otherwise
    """
    if usecwd or '__file__' not in globals():
        # should work without __file__, e.g. in REPL or IPython notebook
        path = os.getcwd()
    elif path:
        pass
    else:
        # will work for .py files
        frame_filename = sys._getframe().f_back.f_code.co_filename
        path = os.path.dirname(os.path.abspath(frame_filename))

    for dirname in _walk_to_root(path):
        check_path = os.path.join(dirname, filename)
        if os.path.exists(check_path):
            return check_path

    if raise_error_if_not_found:
        raise IOError('File not found')

    return ''


def random_password(size=15):
    chars = (string.letters + string.digits + string.punctuation).translate(None, '\'";:@%{}*$/&#?[]`~\\')

    return ''.join((random.choice(chars)) for x in range(size)).replace("'", '-').replace('?', '*')


def compare_dicts(source, destination):
    """
    :type source dict
    :type destination dict
    :return: dict
    """
    source_vars = source.copy()
    destination_vars = destination.copy()

    def prompt(name, source, dest, default):
        return click.prompt(
            click.style(
                '{name}: "{source_value}" -> "{dest_value}"'.format(name=name, source_value=source, dest_value=dest),
                fg='yellow' if val != default else 'green'
            ),
            default=default
        )

    # merge values
    for name in sorted(source_vars.iterkeys()):
        val = source_vars.get(name)
        destination_vars[name] = prompt(
            name, val, destination_vars.get(name, ""),
            val if name not in destination_vars else destination_vars.get(name, "")
        )

    for name in sorted(destination_vars.iterkeys()):
        if name in source_vars:
            continue

        val = click.prompt(
            'Parameter "{}" has been removed from source profile, delete it from destination as well?'.format(name),
            type=Boolean(),
            default=True
        )

        if val:
            del destination_vars[name]

    return destination_vars
