from __future__ import absolute_import
import json
from textwrap import wrap

import click
from pygments import highlight, lexers, formatters
from terminaltables import SingleTable


def colourize(name):
    if name in ["prod", "production"]:
        return click.style(name, fg="red")
    elif name in ["staging", "preprod"]:
        return click.style(name, fg="yellow")
    else:
        return name


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

    max_width = _table.column_max_width(wraped_col)
    for i, val in enumerate(_data):
        wrapped_string = '\n'.join(wrap(str(val[wraped_col]), max_width))
        _table.table_data[i][wraped_col] = wrapped_string

    return _table


def display_section(title, data, title_fg="blue", body_fg="white"):
    click.secho(title.upper() + ": ", fg=title_fg)

    click.secho(data + "\n", fg=body_fg)
